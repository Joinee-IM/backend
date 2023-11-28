from typing import Sequence

from app.base import do, enums
from app.persistence.database.util import PostgresQueryExecutor


async def browse(place_type: enums.PlaceType, place_id: int) -> Sequence[do.Album]:
    results = await PostgresQueryExecutor(
        sql=r'SELECT id, place_id, type, file_uuid'
            r'  FROM album'
            r' WHERE place_id = %(place_id)s AND type = %(place_type)s',
        place_id=place_id, place_type=place_type,
    ).fetch_all()

    return [
        do.Album(
            id=id_,
            place_id=place_id,
            type=place_type,
            file_uuid=file_uuid,
        )
        for id_, place_id, place_type, file_uuid in results
    ]
