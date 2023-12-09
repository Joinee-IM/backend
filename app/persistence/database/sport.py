from typing import Sequence

import app.exceptions as exc
from app.base import do
from app.persistence.database.util import PostgresQueryExecutor


async def browse() -> Sequence[do.Sport]:
    results = await PostgresQueryExecutor(
        sql=r'SELECT sport.id, sport.name'
            r'  FROM sport',
    ).fetch_all()

    return [
        do.Sport(
            id=id_,
            name=name,
        ) for id_, name in results
    ]


async def read(sport_id: int) -> do.Sport:
    try:
        id_, name = await PostgresQueryExecutor(
            sql='SELECT id, name'
                '  FROM sport'
                ' WHERE id = %(sport_id)s',
            sport_id=sport_id,
        ).fetch_one()
    except TypeError:
        raise exc.NotFound

    return do.Sport(id=id_, name=name)
