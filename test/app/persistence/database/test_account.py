from test import AsyncMock, AsyncTestCase
from unittest.mock import patch

import app.exceptions as exc
from app.base.enums import GenderType, RoleType
from app.persistence.database import account


class TestAddAccount(AsyncTestCase):
    def setUp(self) -> None:
        self.happy_path_result = 1

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', AsyncMock(return_value=(1,)))
    async def test_add_account_happy_path(self):
        result = await account.add(
            email='email', pass_hash='pass_hash', nickname='nickname',
            gender=GenderType.unrevealed, role=RoleType.normal, is_google_login=False,
        )
        self.assertEqual(result, self.happy_path_result)

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute',
           AsyncMock(side_effect=exc.UniqueViolationError))
    async def test_add_account_unique_error(self):
        with self.assertRaises(exc.UniqueViolationError):
            await account.add(
                email='email', pass_hash='pass_hash', nickname='nickname',
                gender=GenderType.unrevealed, role=RoleType.normal, is_google_login=False,
            )


class TestReadByEmail(AsyncTestCase):
    def setUp(self) -> None:
        self.email = 'email'
        self.execute_result = 1, 'hash', 'NORMAL'
        self.expect_output = 1, 'hash', RoleType.normal

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock):
        mock_execute.return_value = self.execute_result

        result = await account.read_by_email(self.email)

        self.assertEqual(result, self.expect_output)
