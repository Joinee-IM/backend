from typing import Sequence

from app.base import do
from app.persistence.database.util import PostgresQueryExecutor


async def browse() -> Sequence[do.City]:
    results = await PostgresQueryExecutor(
        sql=r'SELECT city.id, city.name'
            r'  FROM city',
        fetch='all',
    ).execute()

    return [
        do.City(
            id=id_,
            name=name,
        ) for id_, name in results
    ]
