from typing import Sequence

import asyncpg

import app.exceptions as exc
from app.base import do, enums, vo
from app.persistence.database.util import (
    PostgresQueryExecutor,
    generate_query_parameters,
    pg_pool_handler,
)


async def browse(
        name: str | None = None,
        city_id: int | None = None,
        district_id: int | None = None,
        sport_id: int | None = None,
        time_ranges: Sequence[vo.WeekTimeRange] | None = None,
        limit: int = 10,
        offset: int = 0,
        include_unpublished: bool = False,
) -> tuple[Sequence[vo.ViewStadium], int]:
    criteria_dict = {
        'name': (f'%{name}%' if name else None, 'stadium.name LIKE %(name)s'),
        'city_id': (city_id, 'district.city_id = %(city_id)s'),
        'district_id': (district_id, 'district.id = %(district_id)s'),
        'sport_id': (sport_id, 'venue.sport_id = %(sport_id)s'),
        'is_published': (True if not include_unpublished else None, 'stadium.is_published = %(is_published)s'),
    }

    query, params = generate_query_parameters(criteria_dict=criteria_dict)

    raw_or_query = []
    if time_ranges:
        for i, time_range in enumerate(time_ranges):
            time_range: vo.WeekTimeRange
            raw_or_query.append(f"""({' AND '.join([
                f'business_hour.weekday = %(weekday_{i})s',
                f'business_hour.start_time <= %(end_time_{i})s',
                f'business_hour.end_time >= %(start_time_{i})s'
            ])})""")
            params.update({
                f'weekday_{i}': time_range.weekday,
                f'end_time_{i}': time_range.end_time,
                f'start_time_{i}': time_range.start_time,
            })

    or_query = ' OR '.join(raw_or_query)

    where_sql = 'WHERE ' + ' AND '.join(query) if query else ''

    if or_query and where_sql:
        where_sql = where_sql + ' AND ' + or_query
    elif or_query:
        where_sql = 'WHERE ' + or_query

    sql = (
        fr'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id, address,'
        fr'       description, long, lat, stadium.is_published,'
        fr'       city.name,'
        fr'       district.name,'
        fr'       ARRAY_AGG(DISTINCT sport.name),'
        fr'       ARRAY_AGG(DISTINCT business_hour.*)'
        fr'  FROM stadium'
        fr' INNER JOIN district ON stadium.district_id = district.id'
        fr' INNER JOIN city ON district.city_id = city.id'
        fr'  LEFT JOIN venue ON stadium.id = venue.stadium_id'
        fr'  LEFT JOIN sport ON venue.sport_id = sport.id'
        fr'  LEFT JOIN business_hour ON business_hour.place_id = stadium.id'
        fr'                         AND business_hour.type = %(place_type)s'
        fr' {where_sql}'
        fr' GROUP BY stadium.id, city.id, district.id'
        fr' ORDER BY stadium.id'
    )

    results = await PostgresQueryExecutor(
        sql=fr'{sql}'
            fr' LIMIT %(limit)s OFFSET %(offset)s',
        limit=limit, offset=offset, place_type=enums.PlaceType.stadium, **params,
    ).fetch_all()

    record_count, = await PostgresQueryExecutor(
        sql=fr'SELECT COUNT(*)'
            fr'  FROM ({sql}) AS tbl',
        place_type=enums.PlaceType.stadium, **params,
    ).fetch_one()

    return [
        vo.ViewStadium(
            id=id_,
            name=name,
            district_id=district_id,
            contact_number=contact_number,
            description=description,
            owner_id=owner_id,
            address=address,
            long=long,
            lat=lat,
            is_published=is_published,
            city=city,
            district=district,
            sports=[name for name in sport_names if name],
            business_hours=[
                do.BusinessHour(
                    id=bid,
                    place_id=place_id,
                    type=place_type,
                    weekday=weekday,
                    start_time=start_time,
                    end_time=end_time,
                ) for bid, place_id, place_type, weekday, start_time, end_time in business_hours
            ],
        )
        for id_, name, district_id, contact_number, owner_id, address, description, long, lat, is_published, city,
        district, sport_names, business_hours in results
    ], record_count


async def read(stadium_id: int, include_unpublished: bool = False) -> vo.ViewStadium:
    result = await PostgresQueryExecutor(
        sql=fr'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id, address,'
            fr'       description, long, lat, stadium.is_published,'
            fr'       city.name,'
            fr'       district.name,'
            fr'       ARRAY_AGG(DISTINCT sport.name),'
            fr'       ARRAY_AGG(DISTINCT business_hour.*)'
            fr'  FROM stadium'
            fr' INNER JOIN district ON stadium.district_id = district.id'
            fr' INNER JOIN city ON district.city_id = city.id'
            fr'  LEFT JOIN venue ON stadium.id = venue.stadium_id'
            fr'  LEFT JOIN sport ON venue.sport_id = sport.id'
            fr'  LEFT JOIN business_hour ON business_hour.place_id = stadium.id'
            fr'                         AND business_hour.type = %(place_type)s'
            fr' WHERE stadium.id = %(stadium_id)s'
            fr'{" AND stadium.is_published = True" if not include_unpublished else ""}'
            fr' GROUP BY stadium.id, city.id, district.id'
            fr' ORDER BY stadium.id',
        place_type=enums.PlaceType.stadium, stadium_id=stadium_id,
    ).fetch_one()

    try:
        (
            id_, name, district_id, contact_number, owner_id, address, description, long, lat, is_published,
            city, district, sport_names, business_hours,
        ) = result
    except TypeError:
        raise exc.NotFound

    return vo.ViewStadium(
        id=id_,
        name=name,
        district_id=district_id,
        contact_number=contact_number,
        owner_id=owner_id,
        address=address,
        description=description,
        long=long,
        lat=lat,
        is_published=is_published,
        city=city,
        district=district,
        sports=[name for name in sport_names if name],
        business_hours=[
            do.BusinessHour(
                id=bid,
                place_id=place_id,
                type=place_type,
                weekday=weekday,
                start_time=start_time,
                end_time=end_time,
            ) for bid, place_id, place_type, weekday, start_time, end_time in business_hours
        ],
    )


async def edit(
        stadium_id: int,
        name: str | None = None,
        address: str | None = None,
        contact_number: str | None = None,
        time_ranges: Sequence[vo.WeekTimeRange] | None = None,
        is_published: bool | None = None,
) -> None:
    if not time_ranges:
        time_ranges = []

    criteria_dict = {
        'name': (name, 'name = %(name)s'),
        'address': (address, 'address = %(address)s'),
        'contact_number': (contact_number, 'contact_number = %(contact_number)s'),
        'is_published': (is_published, 'is_published = %(is_published)s'),
    }

    query, params = generate_query_parameters(criteria_dict=criteria_dict)

    set_sql = ', '.join(query)

    update_sql, update_param = PostgresQueryExecutor.format(
        sql=fr'UPDATE stadium'
            fr'   SET {set_sql}'
            fr' WHERE id = %(stadium_id)s',
        stadium_id=stadium_id, **params,
    )

    raw_insert_sql = ', '.join(
        f'(%(place_id)s, %(place_type)s, %(weekday_{i})s, %(start_time_{i})s, %(end_time_{i})s)' for i, time_range in
        enumerate(time_ranges)
    )
    raw_params = {f'weekday_{i}': time_range.weekday for i, time_range in enumerate(time_ranges)}
    raw_params.update({f'start_time_{i}': time_range.start_time for i, time_range in enumerate(time_ranges)})
    raw_params.update({f'end_time_{i}': time_range.end_time for i, time_range in enumerate(time_ranges)})

    insert_sql, insert_params = PostgresQueryExecutor.format(
        sql=fr'INSERT INTO business_hour'
            fr'            (place_id, type, weekday, start_time, end_time)'
            fr'     VALUES {raw_insert_sql}',
        place_id=stadium_id, place_type=enums.PlaceType.stadium, **raw_params,
    )

    async with pg_pool_handler.cursor() as cursor:
        cursor: asyncpg.connection.Connection
        if set_sql:
            await cursor.execute(
                update_sql, *update_param,
            )

        if time_ranges:
            await cursor.execute(
                'DELETE FROM business_hour'
                ' WHERE type = $1'
                '   AND place_id = $2',
                enums.PlaceType.stadium, stadium_id,
            )

            await cursor.execute(
                insert_sql, *insert_params,
            )


async def add(
        name: str, address: str, district_id: int,
        owner_id: int, contact_number: str, description: str, long: float, lat: float,
) -> int:
    id_, = await PostgresQueryExecutor(
        sql=r'INSERT INTO stadium(name, district_id, owner_id, address, contact_number, description, long,'
            r'                        lat, is_published)'
            r'                 VALUES(%(name)s, %(district_id)s, %(owner_id)s, %(address)s, %(contact_number)s,'
            r'                        %(description)s, %(long)s, %(lat)s, %(is_published)s)'
            r'  RETURNING id',
        name=name, district_id=district_id, owner_id=owner_id, address=address, contact_number=contact_number,
        description=description, long=long, lat=lat, is_published=True,
    ).fetch_one()
    return id_
