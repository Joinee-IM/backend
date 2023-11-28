from unittest.mock import patch

from app.persistence.database.util import PostgresQueryExecutor, QueryExecutor
from tests import AsyncMock, AsyncTestCase


class MockQueryExecutor(QueryExecutor):
    @staticmethod
    def _format(sql: str, parameters: dict[str, any] = None, **params):
        return "", []

    async def fetch_all(self):
        return 2

    async def fetch_one(self):
        return 1

    async def execute(self):
        return 0


class TestQueryExecutor(AsyncTestCase):
    def setUp(self) -> None:
        self.sql = 'SELECT * FROM account WHERE id = %(account_id)s AND name = %(name)s'  # noqa
        self.params = {'account_id': 1, 'name': 'name'}

    def test_format(self):
        with self.assertRaises(NotImplementedError):
            QueryExecutor._format(sql=self.sql, parameters=self.params)

    async def test_fetch_all(self):
        QueryExecutor.__abstractmethods__ = set()
        with self.assertRaises(NotImplementedError):
            await QueryExecutor(self.sql, fetch='all').fetch_all()

    async def test_fetch_one(self):
        QueryExecutor.__abstractmethods__ = set()
        with self.assertRaises(NotImplementedError):
            await QueryExecutor(self.sql, fetch=1).fetch_one()

    async def test_fetch_none(self):
        QueryExecutor.__abstractmethods__ = set()
        with self.assertRaises(NotImplementedError):
            await QueryExecutor(self.sql, fetch=None).execute()

    @patch('app.persistence.database.util.QueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_execute(self, mock_fetch_one: AsyncMock):
        QueryExecutor.__abstractmethods__ = set()
        mock_fetch_one.side_effect = Exception()
        await MockQueryExecutor(sql=self.sql, fetch=1).execute()


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
            sql=self.sql, **self.params,
        ).fetch_all()
        mock_fetch_all.assert_called_once()
        self.assertEqual(result, 'fake_result')

    @patch('app.log.context', AsyncTestCase.context)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_execute_fetch_one(self, mock_fetch_one):
        mock_fetch_one.return_value = 'fake_result'
        result = await PostgresQueryExecutor(
            sql=self.sql, **self.params,
        ).fetch_one()
        mock_fetch_one.assert_called_once()
        self.assertEqual(result, 'fake_result')

    @patch('app.log.context', AsyncTestCase.context)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_execute_fetch_none(self, mock_fetch_none):
        mock_fetch_none.return_value = None
        result = await PostgresQueryExecutor(
            sql=self.sql, **self.params,
        ).execute()
        mock_fetch_none.assert_called_once()
        self.assertIsNone(result)
