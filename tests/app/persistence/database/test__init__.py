from contextlib import asynccontextmanager
from unittest.mock import patch

from app.config import PGConfig
from app.persistence.database import PGPoolHandler, PoolHandlerBase
from tests import AsyncMock, AsyncTestCase


class MockPoolHandler(PoolHandlerBase):
    async def initialize(self, db_config):
        return await super().initialize(db_config=db_config)

    @asynccontextmanager
    async def cursor(self):
        return await super().cursor()


class TestPoolHandlerBase(AsyncTestCase):
    async def test_initialized(self):
        handler = MockPoolHandler()
        with self.assertRaises(NotImplementedError):
            await handler.initialize(db_config=PGConfig())

    async def test_close(self):
        handler = MockPoolHandler()
        mock_pool = AsyncMock()
        handler._pool = mock_pool
        mock_pool.close = AsyncMock()
        await handler.close()
        self.assertIsNone(handler._pool)


class TestPGPoolHandler(AsyncTestCase):
    def setUp(self) -> None:
        self.mock_pool = 'mock_pool'
        self.config = PGConfig()
        self.handler = PGPoolHandler()

    def tearDown(self) -> None:
        self.handler._pool = None

    @patch('asyncpg.create_pool', new_callable=AsyncMock)
    async def test_initialize(self, mock_create_pool):
        handler = PGPoolHandler()
        mock_create_pool.return_value = self.mock_pool
        await handler.initialize(self.config)
        mock_create_pool.assert_called_with(
            host=self.config.host,
            port=self.config.port,
            user=self.config.username,
            password=self.config.password,
            database=self.config.db_name,
            max_size=self.config.max_pool_size,
            min_size=1,
        )
