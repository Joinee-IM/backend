from datetime import datetime
from typing import Sequence

from app.base import enums, vo
from app.persistence.database.util import (
    PostgresQueryExecutor,
    generate_query_parameters,
)


async def browse_my_reservation(
        account_id: int,
        request_time: datetime,
        is_manager: bool | None = None,
        time_ranges: Sequence[vo.DateTimeRange] | None = None,
        has_vacancy: bool | None = None,
        reservation_status: enums.ReservationStatus | None = None,
        member_status: enums.ReservationMemberStatus | None = None,
        source: enums.ReservationMemberSource | None = None,
        sort_by: enums.ViewMyReservationSortBy = enums.ViewMyReservationSortBy.time,
        order: enums.Sorter = enums.Sorter.desc,
        limit: int = 10,
        offset: int = 0,
) -> tuple[Sequence[vo.ViewMyReservation], int]:
    criteria_dict = {
        'is_manager': (is_manager, 'is_manager = %(is_manager)s'),
        'has_vacancy': (has_vacancy or None, 'vacancy > 0'),
        'member_status': (member_status, 'status = %(member_status)s'),
        'reservation_status': (reservation_status, 'reservation_status = %(reservation_status)s'),
        'source': (source, 'source = %(source)s'),
    }

    query, params = generate_query_parameters(criteria_dict=criteria_dict)

    raw_or_query = []
    if time_ranges:
        for i, time_range in list(enumerate(time_ranges)):
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
        r'       member.is_manager,'
        r'       account.nickname,'
        r'       vacancy,'
        r'       CASE'
        r'           WHEN is_cancelled THEN %(cancelled)s'
        r'           WHEN end_time < %(request_time)s THEN %(finished)s'
        r'           ELSE %(in_progress)s'
        r'       END AS reservation_status,'
        r'       is_cancelled'
        r'  FROM reservation'
        r' INNER JOIN venue ON venue.id = reservation.venue_id'
        r' INNER JOIN stadium ON stadium.id = reservation.stadium_id'
        r' INNER JOIN reservation_member member'
        r'         ON member.reservation_id = reservation.id'
        r'        AND member.account_id = %(account_id)s'
        r' INNER JOIN reservation_member manager'
        r'         ON manager.reservation_id = reservation.id'
        r'        AND manager.is_manager'
        r' INNER JOIN account'
        r'         ON account.id = manager.account_id'
        fr' {where_sql}'
        fr' ORDER BY {sort_by} {order}'
    )

    results = await PostgresQueryExecutor(
        sql=fr'{sql}'
            r' LIMIT %(limit)s OFFSET %(offset)s',
        account_id=account_id, limit=limit, offset=offset, **params,
        request_time=request_time,
        cancelled=enums.ReservationStatus.cancelled,
        finished=enums.ReservationStatus.finished,
        in_progress=enums.ReservationStatus.in_progress,
    ).fetch_all()

    total_count, = await PostgresQueryExecutor(
        sql=fr'SELECT COUNT(*)'
            fr'  FROM ({sql}) AS tbl',
        account_id=account_id, **params,
        request_time=request_time,
        cancelled=enums.ReservationStatus.cancelled,
        finished=enums.ReservationStatus.finished,
        in_progress=enums.ReservationStatus.in_progress,
    ).fetch_one()

    return [
        vo.ViewMyReservation(
            reservation_id=reservation_id,
            start_time=start_time,
            end_time=end_time,
            stadium_name=stadium_name,
            venue_name=venue_name,
            is_manager=is_manager,
            manager_name=manager_name,
            vacancy=vacancy,
            status=reservation_status,
        )
        for reservation_id, start_time, end_time, stadium_name, venue_name, is_manager,
        manager_name, vacancy, reservation_status, is_cancelled in results
    ], total_count


async def browse_provider_stadium(
        owner_id: int,
        city_id: int | None = None,
        district_id: int | None = None,
        is_published: bool | None = None,
        sort_by: enums.ViewProviderStadiumSortBy = enums.ViewProviderStadiumSortBy,
        order: enums.Sorter = enums.Sorter.asc,
        limit: int = None,
        offset: int = None,
) -> tuple[Sequence[vo.ViewProviderStadium], int]:
    criteria_dict = {
        'owner_id': (owner_id, 'owner_id = %(owner_id)s'),
        'city_id': (city_id, 'city_id = %(city_id)s'),
        'district_id': (district_id, 'district_id = %(district_id)s'),
        'is_published': (is_published, 'stadium.is_published = %(is_published)s'),
    }

    query, params = generate_query_parameters(criteria_dict=criteria_dict)
    where_sql = 'WHERE ' + ' AND '.join(query) if query else ''

    sql = (
        fr'SELECT stadium.id AS stadium_id,'
        fr'       city.name AS city_name,'
        fr'       district.name AS district_name,'
        fr'       stadium.name AS stadium_name,'
        fr'       COUNT(venue.*) AS venue_count,'
        fr'       stadium.is_published AS is_published'
        fr'  FROM stadium'
        fr' INNER JOIN district ON district.id = stadium.district_id'
        fr' INNER JOIN city ON city.id = district.city_id'
        fr'  LEFT JOIN venue ON venue.stadium_id = stadium.id'
        fr' {where_sql}'
        fr' GROUP BY stadium.id, city.id, district.id'
    )

    results = await PostgresQueryExecutor(
        sql=fr'{sql}'
            fr' ORDER BY {sort_by} {order}, stadium.id'
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
        vo.ViewProviderStadium(
            stadium_id=stadium_id,
            city_name=city_name,
            district_name=district_name,
            stadium_name=stadium_name,
            venue_count=venue_count,
            is_published=is_published,
        )
        for stadium_id, city_name, district_name, stadium_name, venue_count, is_published in results
    ], total_count


async def browse_provider_venue(
        owner_id: int,
        stadium_id: int | None = None,
        is_published: bool | None = None,
        sort_by: enums.ViewProviderVenueSortBy = enums.ViewProviderVenueSortBy.stadium_name,
        order: enums.Sorter = enums.Sorter.asc,
        limit: int = None,
        offset: int = None,
) -> tuple[Sequence[vo.ViewProviderVenue], int]:
    criteria_dict = {
        'owner_id': (owner_id, 'stadium.owner_id = %(owner_id)s'),
        'stadium_id': (stadium_id, 'stadium_id = %(stadium_id)s'),
        'is_published': (is_published, 'venue.is_published = %(is_published)s'),
    }

    query, params = generate_query_parameters(criteria_dict=criteria_dict)
    where_sql = 'WHERE ' + ' AND '.join(query) if query else ''

    sql = (
        fr'SELECT venue.id,'
        fr'       stadium.name AS stadium_name,'
        fr'       venue.name AS venue_name,'
        fr'       COUNT(court.*) AS court_count,'
        fr'       venue.area AS area,'
        fr'       venue.is_published AS is_published'
        fr'  FROM venue'
        fr' INNER JOIN stadium ON stadium.id = venue.stadium_id'
        fr'  LEFT JOIN court ON venue.id = court.venue_id'
        fr' {where_sql}'
        fr' GROUP BY stadium.id, venue.id'
    )

    results = await PostgresQueryExecutor(
        sql=fr'{sql}'
            fr' ORDER BY {sort_by} {order}, stadium.id, venue.id'
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
        vo.ViewProviderVenue(
            venue_id=venue_id,
            stadium_name=stadium_name,
            venue_name=venue_name,
            court_count=court_count,
            area=area,
            is_published=is_published,
        )
        for venue_id, stadium_name, venue_name, court_count, area, is_published in results
    ], total_count


async def browse_provider_court(
        owner_id: int,
        stadium_id: int | None = None,
        venue_id: int | None = None,
        is_published: bool | None = None,
        sort_by: enums.ViewProviderCourtSortBy = enums.ViewProviderCourtSortBy.stadium_name,
        order: enums.Sorter = enums.Sorter.asc,
        limit: int = None,
        offset: int = None,
) -> tuple[Sequence[vo.ViewProviderCourt], int]:
    criteria_dict = {
        'owner_id': (owner_id, 'stadium.owner_id = %(owner_id)s'),
        'stadium_id': (stadium_id, 'stadium.id = %(stadium_id)s'),
        'venue_id': (venue_id, 'venue.id = %(venue_id)s'),
        'is_published': (is_published, 'court.is_published = %(is_published)s'),
    }

    query, params = generate_query_parameters(criteria_dict=criteria_dict)
    where_sql = 'WHERE ' + ' AND '.join(query) if query else ''

    sql = (
        fr'SELECT court.id AS court_id,'
        fr'       stadium.name AS stadium_name,'
        fr'       venue.name AS venue_name,'
        fr'       court.number AS number,'
        fr'       court.is_published AS is_published'
        fr'  FROM court'
        fr' INNER JOIN venue ON venue.id = court.venue_id'
        fr' INNER JOIN stadium ON stadium.id = venue.stadium_id'
        fr' {where_sql}'
    )

    results = await PostgresQueryExecutor(
        sql=fr'{sql}'
            fr' ORDER BY {sort_by} {order}, stadium.id, venue.id, court.id'
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
        vo.ViewProviderCourt(
            court_id=court_id,
            stadium_name=stadium_name,
            venue_name=venue_name,
            court_number=court_number,
            is_published=is_published,
        )
        for court_id, stadium_name, venue_name, court_number, is_published in results
    ], total_count
