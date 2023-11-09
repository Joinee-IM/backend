from abc import abstractmethod
from uuid import UUID


class BaseFileHandler:
    def __init__(self):
        self.client = None

    @abstractmethod
    def initialize(self):
        raise NotImplementedError

    @abstractmethod
    async def upload(self, file: str, key: UUID, bucket_name: str):
        raise NotImplementedError

    @abstractmethod
    async def sign_url(self, method, bucket_name: str, filename, expire_time):
        raise NotImplementedError
