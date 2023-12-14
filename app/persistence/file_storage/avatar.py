import typing
from uuid import UUID, uuid4

from app.persistence.file_storage.gcs import gcs_handler

BUCKET_NAME = 'cloud-native-storage-db'


async def upload(file: typing.IO, file_uuid: UUID | None = uuid4(), content_type: str = None)\
        -> tuple[UUID, str]:
    return await gcs_handler.upload(
        file=file,
        key=file_uuid,
        bucket_name=BUCKET_NAME,
        content_type=content_type,
    ), BUCKET_NAME
