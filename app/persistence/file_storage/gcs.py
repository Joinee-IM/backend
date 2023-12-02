import typing
from time import time
from uuid import UUID, uuid4

from google.cloud import storage

from app.base import mcs
from app.persistence.file_storage import BaseFileHandler


class GCSHandler(BaseFileHandler, metaclass=mcs.Singleton):
    def __init__(self):
        super().__init__()
        self.client: storage.Client = None  # noqa

    def initialize(self):
        self.client = storage.Client()

    async def upload(self, file: typing.IO, key: UUID = None, bucket_name: str = 'cloud-native-storage-db', content_type: str = None):
        if key is None:
            key = uuid4()
        blob = await self.get_blob(bucket_name=bucket_name, filename=str(key))
        blob.upload_from_file(file, content_type=content_type)
        return key

    async def get_blob(self, bucket_name: str, filename: str) -> storage.blob.Blob:
        bucket = self.client.get_bucket(bucket_name)
        return storage.blob.Blob(bucket=bucket, name=filename)

    async def sign_url(self, filename: str, bucket_name: str = 'cloud-native-storage-db',
                       method: str = 'GET', expire_time: int = 3600):
        blob = await self.get_blob(bucket_name, filename)
        signed_url = blob.generate_signed_url(
            expiration=int(time()) + expire_time,
            response_type='text/plain',
            method=method,
        )
        return signed_url


gcs_handler = GCSHandler()
