from typing import Sequence

from app.base import do, enums
from app.persistence.database.util import (
    PostgresQueryExecutor,
    generate_query_parameters,
)


async def browse(
        name: str | None = None,
        sport_id: int | None = None,
        is_reservable: bool | None = None,
        sort_by: enums.VenueAvailableSortBy | None = None,
        order: enums.Sorter = enums.Sorter.desc,
        limit: int = 10,
        offset: int = 0,
) -> Sequence[do.Venue]:
    criteria_dict = {
        'name': (f'%{name}%' if name else None, 'name LIKE %(name)s'),
        'sport_id': (sport_id, 'sport_id = %(sport_id)s'),
        'is_reservable': (is_reservable, 'is_reservable = %(is_reservable)s'),
    }
    query, params = generate_query_parameters(criteria_dict=criteria_dict)

    where_sql = 'WHERE ' + ' AND '.join(query) if query else ''

    order_sql = f'{sort_by.lower()} {order},'

    results = await PostgresQueryExecutor(
        sql=fr'SELECT id, stadium_id, name, floor, reservation_interval, is_reservable,'
            fr'       is_chargeable, fee_rate, fee_type, area, current_user_count, capability,'
            fr'       sport_equipments, facilities, court_count, court_type, sport_id'
            fr'  FROM venue'
            fr' {where_sql}'
            fr' ORDER BY {order_sql} venue.id'
            fr' LIMIT %(limit)s OFFSET %(offset)s',
        limit=limit, offset=offset, fetch='all', **params,
    ).execute()

    return [
        do.Venue(
            id=id_, stadium_id=stadium_id, name=name, floor=floor, reservation_interval=reservation_interval,
            is_reservable=is_reservable, is_chargeable=is_chargeable, fee_rate=fee_rate, fee_type=fee_type,
            area=area, current_user_count=current_user_count, capability=capability, sport_equipments=sport_equipments,
            facilities=facilities, court_count=court_count, court_type=court_type, sport_id=sport_id,
        )
        for id_, stadium_id, name, floor, reservation_interval, is_reservable,
        is_chargeable, fee_rate, fee_type, area, current_user_count, capability,
        sport_equipments, facilities, court_count, court_type, sport_id in results
    ]
