"""
Controls the connection / driver of database.
------

分類的邏輯：拿出來的東西是什麼，就放在哪個檔案
"""
from abc import abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncContextManager

import asyncpg
import asynch

from base import mcs
from config import PGConfig, CHConfig


_Pool = asyncpg.pool.Pool | asynch.pool.Pool
_Connection = asyncpg.connection.Connection | asynch.connection.Connection
_Cursor = asyncpg.connection.cursor.Cursor | asynch.connection.Cursor


class PoolHandlerBase:
    def __init__(self):
        self._pool: _Pool = None  # noqa

    @abstractmethod
    async def initialize(self, db_config: PGConfig):
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
    async def cursor(self) -> AsyncContextManager[_Cursor]:
        raise NotImplementedError


class ClickhousePoolHandler(PoolHandlerBase, metaclass=mcs.Singleton):
    async def initialize(self, db_config: CHConfig):
        if self._pool is None:
            self._pool = await asynch.create_pool(
                host=db_config.host,
                port=db_config.port,
                user=db_config.username,
                password=db_config.password,
                database=db_config.db_name,
                maxsize=db_config.max_pool_size,
            )

    @asynccontextmanager
    async def cursor(self) -> AsyncContextManager[asynch.connection.Cursor]:
        """
        NOTE: params: dict
        usage:
            async with clickhouse_pool_handler.cursor() as cursor:
                await cursor.execute(sql, params)
                await cursor.fetchall()
        """
        async with self._pool.acquire() as conn:
            conn: _Connection
            async with conn.cursor() as cursor:
                cursor: asynch.connection.Cursor
                yield cursor

    async def close(self):
        if self._pool is not None:
            self._pool.close()
            self._pool = None


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
            )

    @asynccontextmanager
    async def cursor(self) -> AsyncContextManager[asyncpg.connection.Connection]:
        """
        NOTE: params: dict
        usage:
            async with pg_pool_handler.cursor() as cursor():
                result = await cursor.fetch(sql, *params)
                result = await cursor.fetchrow(sql, *params)
                result = await cursor.execute(sql, *params)
        """
        async with self._pool.acquire() as conn:
            conn: asyncpg.connection.Connection
            async with conn.transaction():
                yield conn


pg_pool_handler = PGPoolHandler()
clickhouse_pool_handler = ClickhousePoolHandler()


# For import usage
from . import (
    account,
    s3_file,
)
