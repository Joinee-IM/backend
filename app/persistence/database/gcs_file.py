from uuid import UUID

import app.exceptions as exc
from app.base import do
from app.persistence.database.util import PostgresQueryExecutor


async def add_with_do(gcs_file: do.GCSFile) -> None:
    await PostgresQueryExecutor(
        sql=r"INSERT INTO gcs_file"
            r"            (file_uuid, key, bucket, filename)"
            r"     VALUES (%(uuid)s, %(key)s, %(bucket)s, %(filename)s)",
        uuid=gcs_file.uuid, key=gcs_file.key, bucket=gcs_file.bucket, filename=gcs_file.filename,
    ).execute()


async def add(file_uuid: UUID, key: str, bucket: str, filename: str) -> None:
    await PostgresQueryExecutor(
        sql=r"INSERT INTO gcs_file"
            r"            (file_uuid, key, bucket, filename)"
            r"     VALUES (%(uuid)s, %(key)s, %(bucket)s, %(filename)s)",
        uuid=file_uuid, key=key, bucket=bucket, filename=filename,
    ).execute()


async def read(file_uuid: UUID) -> do.GCSFile:
    try:
        file_uuid, key, bucket, filename = await PostgresQueryExecutor(
            sql=r'SELECT file_uuid, key, bucket, filename'
                r'  FROM gcs_file'
                r' WHERE file_uuid = %(file_uuid)s',
            file_uuid=file_uuid,
        ).fetch_one()
    except TypeError:
        raise exc.NotFound

    return do.GCSFile(
        uuid=file_uuid,
        key=key,
        bucket=bucket,
        filename=filename,
    )
