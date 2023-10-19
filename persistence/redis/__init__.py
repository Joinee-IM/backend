from contextlib import asynccontextmanager
from typing import AsyncContextManager

import aioredis

from config import RedisConfig
from persistence import PoolHandlerBase


class RedisPoolHandler(PoolHandlerBase):
    def __init__(self):
        super().__init__()
        self._redis: aioredis.Redis = None  # noqa

    async def initialize(self, db_config: RedisConfig):
        if self._pool is None:
            self._pool = aioredis.ConnectionPool.from_url(
                db_config.url,
                max_connections=db_config.max_pool_size
            )
            self._redis = aioredis.Redis(connection_pool=self._pool)

    @asynccontextmanager
    async def cursor(self) -> AsyncContextManager:
        """
        usage:
            async with redis_pool_handler.cursor() as cursor:
                await cursor.set('key', 'value')
                await cursor.get('key')
        """
        yield self._redis

    async def close(self):
        if self._pool is not None:
            await self._pool.disconnect()


redis_pool_handler = RedisPoolHandler()
