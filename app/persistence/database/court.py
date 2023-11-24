from typing import Sequence

import app.exceptions as exc
from app.base import do
from app.persistence.database.util import PostgresQueryExecutor


async def read(court_id: int) -> do.Court:
    try:
        id_, venue_id = await PostgresQueryExecutor(
            sql='SELECT id, venue_id'
                '  FROM court'
                ' WHERE id = %(court_id)s',
            court_id=court_id, fetch=1,
        ).execute()
    except TypeError:
        raise exc.NotFound

    return do.Court(id=id_, venue_id=venue_id)


async def browse(venue_id: int) -> Sequence[do.Court]:
    results = await PostgresQueryExecutor(
        sql='SELECT id, venue_id'
            '  FROM court'
            ' WHERE venue_id = %(venue_id)s',
        venue_id=venue_id, fetch='all',
    ).fetch_all()

    return [
        do.Court(
            id=id_,
            venue_id=venue_id,
        )
        for id_, venue_id in results
    ]
