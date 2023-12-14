from datetime import date, datetime, timedelta
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
        city_id: int | None = None,
        district_id: int | None = None,
        stadium_id: int | None = None,
        court_id: int | None = None,
        sport_id: int | None = None,
        time_ranges: Sequence[vo.DateTimeRange] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        technical_level: enums.TechnicalType | None = None,
        has_vacancy: bool | None = None,
        is_cancelled: bool | None = False,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: enums.BrowseReservationSortBy = None,
        order: enums.Sorter = None,
) -> tuple[Sequence[do.Reservation], int]:
    if not end_date and start_date:
        end_date = start_date + timedelta(days=7)
    criteria_dict = {
        'city_id': (city_id, 'city_id = %(city_id)s'),
        'district_id': (district_id, 'district_id = %(district_id)s'),
        'stadium_id': (stadium_id, 'stadium_id = %(stadium_id)s'),
        'court_id': (court_id, 'court_id = %(court_id)s'),
        'sport_id': (sport_id, 'sport_id = %(sport_id)s'),
        'start_date': (start_date, 'start_time >= %(start_date)s'),
        'end_date': (end_date, 'end_time <= %(end_date)s'),
        'technical_level': (technical_level, '%(technical_level)s = ANY(technical_level)'),
        'vacancy': (has_vacancy, 'vacancy > 0'),
        'is_cancelled': (is_cancelled, 'is_cancelled = %(is_cancelled)s'),
    }

    sort_by_dict = {
        'vacancy': 'vacancy',
        'time': 'start_time',
    }

    query, params = generate_query_parameters(criteria_dict=criteria_dict)

    raw_or_query = []
    if time_ranges:
        for i, time_range in enumerate(time_ranges):
            time_range: vo.WeekTimeRange
            raw_or_query.append(f"""({' AND '.join([
                f'reservation.start_time < %(end_time_{i})s',
                f'reservation.end_time > %(start_time_{i})s'
            ])})""")
            params.update({
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
        fr'SELECT reservation.id, reservation.stadium_id, venue_id, court_id, start_time, end_time, member_count,'
        fr'       vacancy, technical_level, remark, invitation_code, is_cancelled'
        fr'  FROM reservation'
        fr' INNER JOIN stadium'
        fr'         ON stadium.id = reservation.stadium_id'
        fr' INNER JOIN district'
        fr'         ON stadium.district_id = district.id'
        fr' INNER JOIN venue'
        fr'         ON venue.id = reservation.venue_id'
        fr' {where_sql}'
        fr' ORDER BY {f"{sort_by_dict[sort_by]} {order}, " if sort_by else ""}start_time'
    )

    results = await PostgresQueryExecutor(
        sql=fr'{sql}'
            fr'{" LIMIT %(limit)s" if limit else ""}'
            fr'{" OFFSET %(offset)s" if offset else ""}',
        **params, limit=limit, offset=offset,
    ).fetch_all()

    total_count, = await PostgresQueryExecutor(
        sql=fr'SELECT COUNT(*)'
            fr'  FROM ({sql}) AS tbl',
        **params,
    ).fetch_one()

    return [
        do.Reservation(
            id=id_,
            stadium_id=stadium_id,
            venue_id=venue_id,
            court_id=court_id,
            start_time=start_time,
            end_time=end_time,
            member_count=member_count,
            vacancy=vacancy,
            technical_level=technical_level,
            remark=remark,
            invitation_code=invitation_code,
            is_cancelled=is_cancelled,
        )
        for id_, stadium_id, venue_id, court_id, start_time, end_time, member_count, vacancy, technical_level,
        remark, invitation_code, is_cancelled in results
    ], total_count


async def add(
        stadium_id: int, venue_id: int, court_id: int, start_time: datetime, end_time: datetime,
        technical_level: Sequence[enums.TechnicalType], invitation_code: str, remark: str = None,
        member_count: int = 0, vacancy: int = -1,
) -> int:
    id_, = await PostgresQueryExecutor(
        sql=r'INSERT INTO reservation(stadium_id, venue_id, court_id, start_time, end_time, member_count, vacancy,'
            r'                        technical_level, remark, invitation_code)'
            r'                 VALUES(%(stadium_id)s, %(venue_id)s, %(court_id)s, %(start_time)s, %(end_time)s,'
            r'                        %(member_count)s, %(vacancy)s, %(technical_level)s, %(remark)s,'
            r'                        %(invitation_code)s)'
            r'  RETURNING id',
        stadium_id=stadium_id, venue_id=venue_id, court_id=court_id, start_time=start_time, end_time=end_time,
        member_count=member_count, vacancy=vacancy, technical_level=technical_level, remark=remark,
        invitation_code=invitation_code,
    ).fetch_one()
    return id_


async def read(reservation_id: int) -> do.Reservation:
    reservation = await PostgresQueryExecutor(
        sql=r'SELECT id, stadium_id, venue_id, court_id, start_time, end_time, member_count,'
            r'       vacancy, technical_level, remark, invitation_code, is_cancelled, google_event_id'
            r'  FROM reservation'
            r' WHERE id = %(reservation_id)s',
        reservation_id=reservation_id,
    ).fetch_one()

    try:
        id_, stadium_id, venue_id, court_id, start_time, end_time, member_count, vacancy, technical_level, \
            remark, invitation_code, is_cancelled, google_event_id = reservation
    except TypeError:
        raise exc.NotFound

    return do.Reservation(
        id=id_,
        stadium_id=stadium_id,
        venue_id=venue_id,
        court_id=court_id,
        start_time=start_time,
        end_time=end_time,
        member_count=member_count,
        vacancy=vacancy,
        technical_level=technical_level,
        remark=remark,
        invitation_code=invitation_code,
        is_cancelled=is_cancelled,
        google_event_id=google_event_id,
    )


async def read_by_code(invitation_code: str) -> do.Reservation:
    reservation = await PostgresQueryExecutor(
        sql=r'SELECT id, stadium_id, venue_id, court_id, start_time, end_time, member_count,'
            r'       vacancy, technical_level, remark, invitation_code, is_cancelled'
            r'  FROM reservation'
            r' WHERE invitation_code = %(invitation_code)s',
        invitation_code=invitation_code,
    ).fetch_one()

    try:
        id_, stadium_id, venue_id, court_id, start_time, end_time, member_count, vacancy, technical_level, \
            remark, invitation_code, is_cancelled = reservation
    except TypeError:
        raise exc.NotFound

    return do.Reservation(
        id=id_,
        stadium_id=stadium_id,
        venue_id=venue_id,
        court_id=court_id,
        start_time=start_time,
        end_time=end_time,
        member_count=member_count,
        vacancy=vacancy,
        technical_level=technical_level,
        remark=remark,
        invitation_code=invitation_code,
        is_cancelled=is_cancelled,
    )


async def add_event_id(reservation_id: int, event_id: str):
    await PostgresQueryExecutor(
        sql=r"UPDATE reservation"
            r"   SET google_event_id = %(event_id)s"
            r" WHERE id = %(reservation_id)s",
        reservation_id=reservation_id, event_id=event_id,
    ).execute()


async def get_manager_id(reservation_id: int):
    try:
        account_id, = await PostgresQueryExecutor(
            sql=r"SELECT reservation_member.account_id"
                r"  FROM reservation"
                r" INNER JOIN reservation_member ON reservation_member.reservation_id = reservation.id"
                r" WHERE reservation.id = %(reservation_id)s AND reservation_member.is_manager = TRUE",
            reservation_id=reservation_id,
        ).fetch_one()
    except TypeError:
        raise exc.NotFound

    return account_id


async def delete(reservation_id: int) -> None:
    async with pg_pool_handler.cursor() as cursor:
        cursor: asyncpg.Connection
        await cursor.execute(
            'DELETE FROM reservation_member'
            ' WHERE reservation_id = $1',
            reservation_id,
        )
        await cursor.execute(
            'DELETE FROM reservation'
            ' WHERE id = $1',
            reservation_id,
        )


async def edit(
        reservation_id: int,
        stadium_id: int | None = None,
        venue_id: int | None = None,
        court_id: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        vacancy: int | None = None,
        technical_levels: Sequence[enums.TechnicalType] | None = None,
        remark: str | None = None,
):
    criteria_dict = {
        'stadium_id': (stadium_id, 'stadium_id = %(stadium_id)s'),
        'venue_id': (venue_id, 'venue_id = %(venue_id)s'),
        'court_id': (court_id, 'court_id = %(court_id)s'),
        'start_time': (start_time, 'start_time = %(start_time)s'),
        'end_time': (end_time, 'end_time = %(end_time)s'),
        'vacancy': (vacancy, 'vacancy = %(vacancy)s'),
        'technical_level': (technical_levels, 'technical_level = %(technical_level)s'),
        'remark': (remark, 'remark = %(remark)s'),
    }

    query, params = generate_query_parameters(criteria_dict=criteria_dict)
    set_sql = ', '.join(query)

    if not set_sql:
        return

    await PostgresQueryExecutor(
        sql=fr'UPDATE reservation'
            fr'   SET {set_sql}'
            fr' WHERE id = %(reservation_id)s',
        **params, reservation_id=reservation_id, fetch=None,
    ).execute()
