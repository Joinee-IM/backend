from datetime import date, timedelta
from typing import Optional, Sequence

from app.base import do, enums, vo
from app.persistence.database.util import (PostgresQueryExecutor,
                                           generate_query_parameters)


async def browse_by_court_id(
        court_id: int,
        time_ranges: Sequence[vo.DateTimeRange] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        is_cancelled: Optional[bool] = False,
) -> Sequence[do.Reservation]:
    if not end_date and start_date:
        end_date = start_date + timedelta(days=7)
    criteria_dict = {
        'court_id': (court_id, 'court_id = %(court_id)s'),
        'start_date': (start_date, 'start_time >= %(start_date)s'),
        'end_date': (end_date, 'end_time <= %(end_date)s'),
        'is_cancelled': (is_cancelled, 'is_cancelled = %(is_cancelled)s'),
    }

    query, params = generate_query_parameters(criteria_dict=criteria_dict)

    raw_or_query = []
    if time_ranges:
        for i, time_range in enumerate(time_ranges):
            time_range: vo.WeekTimeRange
            raw_or_query.append(f"""({' AND '.join([
                f'reservation.start_time <= %(end_time_{i})s',
                f'reservation.end_time >= %(start_time_{i})s'
            ])})""")
            params.update({
                f'end_time_{i}': time_range.end_time,
                f'start_time_{i}': time_range.start_time
            })

    or_query = ' OR '.join(raw_or_query)

    where_sql = 'WHERE ' + ' AND '.join(query) if query else ''
    where_sql += (' AND ' if where_sql else 'WHERE ') + or_query if or_query else ''

    results = await PostgresQueryExecutor(
        sql=fr'SELECT id, stadium_id, venue_id, court_id, start_time, end_time, member_count,'
            fr'       vacancy, technical_level, remark, invitation_code, is_cancelled'
            fr'  FROM reservation'
            fr' {where_sql}'
            fr' ORDER BY start_time',
        fetch='all', **params,
    ).execute()

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
            technical_level=[enums.TechnicalType(t) for t in technical_level],
            remark=remark,
            invitation_code=invitation_code,
            is_cancelled=is_cancelled,
        )
        for id_, stadium_id, venue_id, court_id, start_time, end_time, member_count, vacancy, technical_level,
        remark, invitation_code, is_cancelled in results
    ]
