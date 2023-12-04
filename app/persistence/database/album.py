from typing import Sequence
from uuid import UUID

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


async def batch_add(place_type: enums.PlaceType, place_id: int, uuids: Sequence[UUID]):
    value_sql = ', '.join(f'(%(place_type)s, %(place_id)s, %(file_uuid_{i})s)' for i, _ in enumerate(uuids))
    params = {f'file_uuid_{i}': file_uuid for i, file_uuid in enumerate(uuids)}
    await PostgresQueryExecutor(
        sql=fr'INSERT INTO album'
            fr'            (type, place_id, file_uuid)'
            fr'     VALUES {value_sql}',
        place_type=place_type, place_id=place_id, **params,
    ).execute()


async def batch_delete(place_type: enums.PlaceType, place_id: int, uuids: Sequence[UUID]):
    params = {fr'uuid_{i}': uuid for i, uuid in enumerate(uuids)}
    in_sql = ", ".join([fr'%({param})s' for param in params])

    await PostgresQueryExecutor(
        sql=fr'DELETE FROM album'
            fr' WHERE place_id = %(place_id)s'
            fr'   AND type = %(place_type)s'
            fr'   AND file_uuid IN ({in_sql})',
        place_id=place_id, place_type=place_type, **params,
    ).execute()
