from unittest.mock import patch

from persistence.database import account
from util.mock import AsyncMock, AsyncTestCase
import exceptions as exc


class TestAddAccount(AsyncTestCase):
    def setUp(self) -> None:
        self.happy_path_result = 1

    @patch('persistence.database.util.PostgresQueryExecutor.execute', AsyncMock(return_value=(1,)))
    @patch('log.context', AsyncTestCase.context)
    async def test_add_account_happy_path(self):
        result = await account.add('test', 'test')
        self.assertEqual(result, self.happy_path_result)

    @patch('persistence.database.util.PostgresQueryExecutor.execute',
           AsyncMock(side_effect=exc.UniqueViolationError))
    @patch('log.context', AsyncTestCase.context)
    async def test_add_account_unique_error(self):
        with self.assertRaises(exc.UniqueViolationError):
            await account.add('test', 'hash')
