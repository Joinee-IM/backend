from app.base import do
from app.persistence.database.util import PostgresQueryExecutor


async def add(gcs_file: do.GCSFile) -> None:
    await PostgresQueryExecutor(
        sql=r"INSERT INTO gcs_file"
            r"            (file_uuid, key, bucket, filename)"
            r"     VALUES (%(uuid)s, %(key)s, %(bucket)s, %(filename)s)",
        uuid=gcs_file.uuid, key=gcs_file.key, bucket=gcs_file.bucket, filename=gcs_file.filename, fetch=None,
    ).execute()
