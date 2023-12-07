from typing import Optional, Sequence

import app.exceptions as exc
from app.base import do, enums
from app.persistence.database.util import (
    PostgresQueryExecutor,
    generate_query_parameters,
)


async def browse(
        name: str | None = None,
        sport_id: int | None = None,
        stadium_id: int | None = None,
        is_reservable: bool | None = None,
        sort_by: enums.VenueAvailableSortBy | None = None,
        order: enums.Sorter = enums.Sorter.desc,
        limit: int = 10,
        offset: int = 0,
        include_unpublished: bool = False,
) -> tuple[Sequence[do.Venue], int]:
    criteria_dict = {
        'name': (f'%{name}%' if name else None, 'name LIKE %(name)s'),
        'sport_id': (sport_id, 'sport_id = %(sport_id)s'),
        'stadium_id': (stadium_id, 'stadium_id = %(stadium_id)s'),
        'is_reservable': (is_reservable, 'is_reservable = %(is_reservable)s'),
        'is_published': (True if not include_unpublished else None, 'venue.is_published = %(is_published)s AND court.is_published = %(is_published)s'),  # noqa
    }
    query, params = generate_query_parameters(criteria_dict=criteria_dict)

    where_sql = 'WHERE ' + ' AND '.join(query) if query else ''

    order_sql = f'{sort_by.lower()} {order},'

    sql = (
        fr'SELECT venue.id, stadium_id, name, floor, reservation_interval, is_reservable,'
        fr'       is_chargeable, fee_rate, fee_type, area, current_user_count, capacity,'
        fr'       sport_equipments, facilities, COUNT(court.*) AS court_count, court_type, sport_id, venue.is_published'
        fr'  FROM venue'
        fr'  LEFT JOIN court ON court.venue_id = venue.id'
        fr' {where_sql}'
        fr' GROUP BY venue.id'
    )

    results = await PostgresQueryExecutor(
        sql=fr'{sql}'
            fr' ORDER BY {order_sql} venue.id'
            fr' LIMIT %(limit)s OFFSET %(offset)s',
        limit=limit, offset=offset, **params,
    ).fetch_all()

    record_count, = await PostgresQueryExecutor(
        sql=fr'SELECT COUNT(*)'
            fr'  FROM ({sql}) AS tbl',
        **params,
    ).fetch_one()

    return [
        do.Venue(
            id=id_, stadium_id=stadium_id, name=name, floor=floor, reservation_interval=reservation_interval,
            is_reservable=is_reservable, is_chargeable=is_chargeable, fee_rate=fee_rate, fee_type=fee_type,
            area=area, current_user_count=current_user_count, capacity=capacity, sport_equipments=sport_equipments,
            facilities=facilities, court_count=court_count, court_type=court_type, sport_id=sport_id,
            is_published=is_published,
        )
        for id_, stadium_id, name, floor, reservation_interval, is_reservable,
        is_chargeable, fee_rate, fee_type, area, current_user_count, capacity,
        sport_equipments, facilities, court_count, court_type, sport_id, is_published in results
    ], record_count


async def read(venue_id: int, include_unpublished: bool = False) -> do.Venue:
    result = await PostgresQueryExecutor(
        sql=fr'SELECT venue.id, stadium_id, name, floor, reservation_interval, is_reservable,'
            fr'       is_chargeable, fee_rate, fee_type, area, current_user_count, capacity,'
            fr'       sport_equipments, facilities, COUNT(court.*) AS court_count, '
            fr'       court_type, sport_id, venue.is_published'
            fr'  FROM venue'
            fr'  LEFT JOIN court ON court.venue_id = venue.id'
            fr' WHERE venue.id = %(venue_id)s'
            fr'{" AND venue.is_published" if not include_unpublished else ""}'
            fr'{" AND court.is_published" if not include_unpublished else ""}'
            fr' GROUP BY venue.id',
        venue_id=venue_id,
    ).fetch_one()

    try:
        (
            id_, stadium_id, name, floor, reservation_interval, is_reservable, is_chargeable, fee_rate, fee_type, area,
            current_user_count, capacity, sport_equipments, facilities, court_count, court_type, sport_id,
            is_published,
        ) = result
    except TypeError:
        raise exc.NotFound

    return do.Venue(
        id=id_,
        stadium_id=stadium_id,
        name=name,
        floor=floor,
        reservation_interval=reservation_interval,
        is_reservable=is_reservable,
        is_chargeable=is_chargeable,
        fee_rate=fee_rate,
        fee_type=fee_type,
        area=area,
        current_user_count=current_user_count,
        capacity=capacity,
        sport_equipments=sport_equipments,
        facilities=facilities,
        court_count=court_count,
        court_type=court_type,
        sport_id=sport_id,
        is_published=is_published,
    )


async def edit(
        venue_id: int,
        name: str | None = None,
        floor: str | None = None,
        area: int | None = None,
        capacity: int | None = None,
        sport_id: int | None = None,
        is_reservable: int | None = None,
        reservation_interval: int | None = None,
        is_chargeable: bool | None = None,
        fee_rate: float | None = None,
        fee_type: enums.FeeType | None = None,
        sport_equipments: str | None = None,
        facilities: str | None = None,
        court_type: str | None = None,
) -> None:
    criteria_dict = {
        'name': (name, 'name = %(name)s'),
        'floor': (floor, 'floor = %(floor)s'),
        'area': (area, 'area = %(area)s'),
        'capacity': (capacity, 'capacity = %(capacity)s'),
        'sport_id': (sport_id, 'sport_id = %(sport_id)s'),
        'is_reservable': (is_reservable, 'is_reservable = %(is_reservable)s'),
        'reservation_interval': (reservation_interval, 'reservation_interval = %(reservation_interval)s'),
        'is_chargeable': (is_chargeable, 'is_chargeable = %(is_chargeable)s'),
        'fee_rate': (fee_rate, 'fee_rate = %(fee_rate)s'),
        'fee_type': (fee_type, 'fee_type = %(fee_type)s'),
        'sport_equipments': (sport_equipments, 'sport_equipments = %(sport_equipments)s'),
        'facilities': (facilities, 'facilities = %(facilities)s'),
        'court_type': (court_type, 'court_type = %(court_type)s'),
    }

    query, params = generate_query_parameters(criteria_dict=criteria_dict)
    set_sql = ', '.join(query)

    await PostgresQueryExecutor(
        sql=fr'UPDATE venue'
            fr'   SET {set_sql}'
            fr' WHERE id = %(venue_id)s',
        venue_id=venue_id, **params,
    ).execute()


async def add(
    stadium_id: int,
    name: str,
    floor: str,
    reservation_interval: Optional[int],
    is_reservable: bool,
    is_chargeable: bool,
    fee_rate: Optional[float],
    fee_type: Optional[enums.FeeType],
    area: int,
    capacity: int,
    sport_equipments: Optional[str],
    facilities: Optional[str],
    court_count: int,
    court_type: str,
    sport_id: int,
) -> int:
    id_, = await PostgresQueryExecutor(
        sql=r'INSERT INTO venue(stadium_id, name, floor, reservation_interval, is_reservable, is_chargeable, fee_rate,'
            r'                  fee_type, area, capacity, sport_equipments, facilities, court_count, court_type, sport_id, is_published)'
            r'              VALUES(%(stadium_id)s, %(name)s, %(floor)s, %(reservation_interval)s, %(is_reservable)s,'
            r'                        %(is_chargeable)s, %(fee_rate)s, %(fee_type)s, %(area)s,'
            r'                          %(capacity)s, %(sport_equipments)s, %(facilities)s, %(court_count)s, %(court_type)s, %(sport_id)s,'
            r'                              %(is_published)s)'
            r'  RETURNING id',
        stadium_id=stadium_id, name=name, floor=floor, reservation_interval=reservation_interval, is_reservable=is_reservable,
        is_chargeable=is_chargeable, fee_rate=fee_rate, fee_type=fee_type, area=area, capacity=capacity, sport_equipments=sport_equipments,
        facilities=facilities, court_count=court_count, court_type=court_type, sport_id=sport_id, is_published=True,
    ).fetch_one()
    return id_
