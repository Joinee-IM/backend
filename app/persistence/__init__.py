from abc import abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncContextManager

from app.config import PGConfig


class PoolHandlerBase:
    def __init__(self):
        self._pool: _Pool = None  # noqa

    @abstractmethod
    async def initialize(self, db_config):
        raise NotImplementedError

    async def close(self):
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    @property
    def pool(self):
        return self._pool

    @abstractmethod
    @asynccontextmanager
    async def cursor(self) -> AsyncContextManager:
        raise NotImplementedError
