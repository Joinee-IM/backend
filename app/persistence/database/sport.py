from typing import Sequence

from app.base import do
from app.persistence.database.util import PostgresQueryExecutor


async def browse() -> Sequence[do.Sport]:
    results = await PostgresQueryExecutor(
        sql=r'SELECT sport.id, sport.name'
            r'  FROM sport',
        fetch='all',
    ).execute()

    return [
        do.Sport(
            id=id_,
            name=name,
        ) for id_, name in results
    ]
