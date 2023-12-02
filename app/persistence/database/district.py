from typing import Sequence

from app.base import do
from app.persistence.database.util import PostgresQueryExecutor


async def browse(city_id: int) -> Sequence[do.District]:
    results = await PostgresQueryExecutor(
        sql=r'SELECT district.id, district.name, district.city_id'
            r'  FROM district'
            r' WHERE district.city_id = %(city_id)s',
        city_id=city_id,
    ).fetch_all()

    return [
        do.District(
            id=id_,
            name=name,
            city_id=city_id,
        ) for id_, name, city_id in results
    ]
