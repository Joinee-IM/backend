from typing import Sequence

from app.base import enums, vo
from app.persistence.database.util import PostgresQueryExecutor
from app.utils.reservation_status import compose_reservation_status


async def browse_my_reservation(
        account_id: int,
        sort_by: enums.ViewMyReservationSortBy,
        order: enums.Sorter,
        limit: int,
        offset: int,
) -> tuple[Sequence[vo.ViewMyReservation], int]:

    if sort_by is enums.ViewMyReservationSortBy.status:
        sort_by = '(start_time, is_cancelled)'
    if sort_by is enums.ViewMyReservationSortBy.time:
        sort_by = 'start_time'

    sql = (
        r'SELECT reservation.id AS reservation_id,'
        r'       start_time,'
        r'       end_time,'
        r'       stadium.name AS stadium_name,'
        r'       venue.name AS venue_name,'
        r'       is_manager,'
        r'       vacancy,'
        r'       is_cancelled'
        r'  FROM reservation'
        r' INNER JOIN venue ON venue.id = reservation.venue_id'
        r' INNER JOIN stadium ON stadium.id = reservation.stadium_id'
        r' INNER JOIN reservation_member'
        r'         ON reservation_member.reservation_id = reservation.id'
        r'        AND reservation_member.account_id = %(account_id)s'
        fr' ORDER BY {sort_by} {order}'
    )

    results = await PostgresQueryExecutor(
        sql=fr'{sql}'
            r' LIMIT %(limit)s OFFSET %(offset)s',
        account_id=account_id, limit=limit, offset=offset,
    ).fetch_all()

    total_count, = await PostgresQueryExecutor(
        sql=fr'SELECT COUNT(*)'
            fr'  FROM ({sql}) AS tbl',
        account_id=account_id,
    ).fetch_one()

    return [
        vo.ViewMyReservation(
            reservation_id=reservation_id,
            start_time=start_time,
            end_time=end_time,
            stadium_name=stadium_name,
            venue_name=venue_name,
            is_manager=is_manager,
            vacancy=vacancy,
            status=compose_reservation_status(end_time=end_time, is_cancelled=is_cancelled),
        )
        for reservation_id, start_time, end_time, stadium_name, venue_name, is_manager, vacancy, is_cancelled in results
    ], total_count
