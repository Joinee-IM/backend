from tests import AsyncMock, AsyncTestCase
from unittest.mock import patch

from app.persistence.database.util import PostgresQueryExecutor, QueryExecutor
from parameterized import parameterized


class MockQueryExecutor(QueryExecutor):
    @staticmethod
    def _format(sql: str, parameters: dict[str, any] = None, **params):
        return "", []

    async def fetch_all(self):
        return 2

    async def fetch_one(self):
        return 1

    async def fetch_none(self):
        return 0


class TestQueryExecutor(AsyncTestCase):
    def setUp(self) -> None:
        self.sql = 'SELECT * FROM account WHERE id = %(account_id)s AND name = %(name)s'  # noqa
        self.params = {'account_id': 1, 'name': 'name'}

    def test_format(self):
        with self.assertRaises(NotImplementedError):
            QueryExecutor._format(sql=self.sql, parameters=self.params)

    async def test_fetch_all(self):
        QueryExecutor.__abstracemethods__ = set()
        with self.assertRaises(NotImplementedError):
            await QueryExecutor(self.sql, fetch='all').fetch_all()

    async def test_fetch_one(self):
        QueryExecutor.__abstracemethods__ = set()
        with self.assertRaises(NotImplementedError):
            await QueryExecutor(self.sql, fetch=1).fetch_one()

    async def test_fetch_none(self):
        QueryExecutor.__abstracemethods__ = set()
        with self.assertRaises(NotImplementedError):
            await QueryExecutor(self.sql, fetch=0).fetch_none()

    @parameterized.expand([
        (None, 0),
        (0, 0),
        (1, 1),
        ('one', 1),
        ('all', 2)
    ])
    async def test_execute(self, fetch, expect_result: int):
        executor = MockQueryExecutor(sql=self.sql, parameters=self.params, fetch=fetch)
        result = await executor.execute()
        self.assertEqual(result, expect_result)


class TestPostgresQueryExecutor(AsyncTestCase):
    def setUp(self) -> None:
        self.sql = 'SELECT * FROM account WHERE id = %(account_id)s AND name = %(name)s'  # noqa
        self.params = {'account_id': 1, 'name': 'name'}
        self._format_expect_output = (
            'SELECT * FROM account WHERE id = $1 AND name = $2', list(self.params.values()),  # noqa
        )

    @patch('app.log.context', AsyncTestCase.context)
    async def test__format(self):
        result = PostgresQueryExecutor._format(
            sql=self.sql, parameters=self.params,
        )
        self.assertEqual(result, self._format_expect_output)

    @patch('app.log.context', AsyncTestCase.context)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    async def test_execute_fetch_all(self, mock_fetch_all):
        mock_fetch_all.return_value = 'fake_result'
        result = await PostgresQueryExecutor(
            sql=self.sql, **self.params, fetch='all'
        ).execute()
        mock_fetch_all.assert_called_once()
        self.assertEqual(result, 'fake_result')

    @patch('app.log.context', AsyncTestCase.context)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_execute_fetch_one(self, mock_fetch_one):
        mock_fetch_one.return_value = 'fake_result'
        result = await PostgresQueryExecutor(
            sql=self.sql, **self.params, fetch=1,
        ).execute()
        mock_fetch_one.assert_called_once()
        self.assertEqual(result, 'fake_result')

    @patch('app.log.context', AsyncTestCase.context)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_none', new_callable=AsyncMock)
    async def test_execute_fetch_none(self, mock_fetch_none):
        mock_fetch_none.return_value = None
        result = await PostgresQueryExecutor(
            sql=self.sql, **self.params, fetch=0,
        ).execute()
        mock_fetch_none.assert_called_once()
        self.assertIsNone(result)
