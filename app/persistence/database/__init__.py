"""
Controls the connection / driver of database.
------

分類的邏輯：拿出來的東西是什麼，就放在哪個檔案
"""
from contextlib import asynccontextmanager
from typing import AsyncContextManager

import asyncpg

from app.base import mcs
from app.config import PGConfig
from app.persistence import PoolHandlerBase


class PGPoolHandler(PoolHandlerBase, metaclass=mcs.Singleton):
    async def initialize(self, db_config: PGConfig):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=db_config.host,
                port=db_config.port,
                user=db_config.username,
                password=db_config.password,
                database=db_config.db_name,
                max_size=db_config.max_pool_size,
                min_size=1,
            )

    @asynccontextmanager
    async def cursor(self) -> AsyncContextManager[asyncpg.connection.Connection]:
        """
        NOTE: params: dict
        usage:
            async with pg_pool_handler.cursor() as cursor:
                result = await cursor.fetch(sql, *params)
                result = await cursor.fetchrow(sql, *params)
                result = await cursor.execute(sql, *params)
        """
        async with self._pool.acquire() as conn:
            conn: asyncpg.connection.Connection
            async with conn.transaction():
                yield conn


pg_pool_handler = PGPoolHandler()

# For import usage
from . import account, city, email_verification, gcs_file, stadium
