from typing import Sequence

import app.exceptions as exc
from app.base import do, enums, vo
from app.persistence.database.util import (PostgresQueryExecutor,
                                           generate_query_parameters)


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
