from typing import Sequence

from app.base import enums, vo
from app.persistence.database.util import (PostgresQueryExecutor,
                                           generate_query_parameters)
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
            fr' ORDER BY {sort_by} {order}'
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


async def browse_provider_venues(
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
            fr' ORDER BY {sort_by} {order}'
            fr'{" LIMIT = %(limit)s" if limit else ""}'
            fr'{" OFFSET = %(offset)s" if offset else ""}',
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
