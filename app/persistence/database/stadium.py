from typing import Sequence

import app.exceptions as exc
from app.base import do, enums, vo
from app.persistence.database.util import (
    PostgresQueryExecutor,
    generate_query_parameters,
)


async def browse(
        name: str | None = None,
        city_id: int | None = None,
        district_id: int | None = None,
        sport_id: int | None = None,
        time_ranges: Sequence[vo.WeekTimeRange] | None = None,
        limit: int = 10,
        offset: int = 0,
) -> tuple[Sequence[vo.ViewStadium], int]:
    criteria_dict = {
        'name': (f'%{name}%' if name else None, 'stadium.name LIKE %(name)s'),
        'city_id': (city_id, 'district.city_id = %(city_id)s'),
        'district_id': (district_id, 'district.id = %(district_id)s'),
        'sport_id': (sport_id, 'venue.sport_id = %(sport_id)s'),
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
                f'start_time_{i}': time_range.start_time
            })

    or_query = ' OR '.join(raw_or_query)

    where_sql = 'WHERE ' + ' AND '.join(query) if query else ''

    where_sql += (' AND ' if where_sql else 'WHERE ') + or_query if or_query else ''

    sql = (
        fr'SELECT stadium.id, stadium.name, district_id, contact_number,'
        fr'       description, long, lat,'
        fr'       city.name,'
        fr'       district.name,'
        fr'       ARRAY_AGG(DISTINCT sport.name),'
        fr'       ARRAY_AGG(DISTINCT business_hour.*)'
        fr'  FROM stadium'
        fr' INNER JOIN district ON stadium.district_id = district.id'
        fr' INNER JOIN city ON district.city_id = city.id'
        fr' INNER JOIN venue ON stadium.id = venue.stadium_id'
        fr' INNER JOIN sport ON venue.sport_id = sport.id'
        fr' INNER JOIN business_hour ON business_hour.place_id = stadium.id'
        fr'                         AND business_hour.type = %(place_type)s'
        fr' {where_sql}'
        fr' GROUP BY stadium.id, city.id, district.id'
        fr' ORDER BY stadium.id'
    )

    results = await PostgresQueryExecutor(
        sql=fr'{sql}'
            fr' LIMIT %(limit)s OFFSET %(offset)s',
        limit=limit, offset=offset, place_type=enums.PlaceType.stadium, fetch='all', **params,
    ).execute()

    record_count, = await PostgresQueryExecutor(
        sql=fr'SELECT COUNT(*)'
            fr'  FROM ({sql}) AS tbl',
        place_type=enums.PlaceType.stadium, fetch=1, **params,
    ).fetch_one()

    return [
        vo.ViewStadium(
            id=id_,
            name=name,
            district_id=district_id,
            contact_number=contact_number,
            description=description,
            long=long,
            lat=lat,
            city=city,
            district=district,
            sports=[name for name in sport_names],
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
        for id_, name, district_id, contact_number, description, long, lat, city, district,
        sport_names, business_hours in results
    ], record_count


async def read(stadium_id: int) -> vo.ViewStadium:
    result = await PostgresQueryExecutor(
        sql=fr'SELECT stadium.id, stadium.name, district_id, contact_number,'
            fr'       description, long, lat,'
            fr'       city.name,'
            fr'       district.name,'
            fr'       ARRAY_AGG(DISTINCT sport.name),'
            fr'       ARRAY_AGG(DISTINCT business_hour.*)'
            fr'  FROM stadium'
            fr' INNER JOIN district ON stadium.district_id = district.id'
            fr' INNER JOIN city ON district.city_id = city.id'
            fr' INNER JOIN venue ON stadium.id = venue.stadium_id'
            fr' INNER JOIN sport ON venue.sport_id = sport.id'
            fr' INNER JOIN business_hour ON business_hour.place_id = stadium.id'
            fr'                         AND business_hour.type = %(place_type)s'
            fr' WHERE stadium.id = %(stadium_id)s'
            fr' GROUP BY stadium.id, city.id, district.id'
            fr' ORDER BY stadium.id',
        fetch=1, place_type=enums.PlaceType.stadium, stadium_id=stadium_id,
    ).execute()

    try:
        id_, name, district_id, contact_number, description, long, lat, city, district, sport_names, business_hours = result
    except TypeError:
        raise exc.NotFound

    return vo.ViewStadium(
        id=id_,
        name=name,
        district_id=district_id,
        contact_number=contact_number,
        description=description,
        long=long,
        lat=lat,
        city=city,
        district=district,
        sports=[name for name in sport_names],
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
