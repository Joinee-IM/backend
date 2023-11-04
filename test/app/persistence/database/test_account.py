from test import AsyncMock, AsyncTestCase
from unittest.mock import patch

import app.exceptions as exc
from app.base import do
from app.base.enums import GenderType, RoleType
from app.persistence.database import account


class TestAddAccount(AsyncTestCase):
    def setUp(self) -> None:
        self.happy_path_result = 1

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', AsyncMock(return_value=(1,)))
    async def test_add_account_happy_path(self):
        result = await account.add(
            email='email@email.com', pass_hash='pass_hash', nickname='nickname',
            gender=GenderType.unrevealed, role=RoleType.normal, is_google_login=False,
        )
        self.assertEqual(result, self.happy_path_result)

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute',
           AsyncMock(side_effect=exc.UniqueViolationError))
    async def test_add_account_unique_error(self):
        with self.assertRaises(exc.UniqueViolationError):
            await account.add(
                email='email@email.com', pass_hash='pass_hash', nickname='nickname',
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

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_not_found(self, mock_execute: AsyncMock):
        mock_execute.return_value = None
        with self.assertRaises(exc.NotFound):
            await account.read_by_email(self.email)


class TestRead(AsyncTestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.expect_result = do.Account(
            id=1, email='email@email.com', nickname='nickname', gender=GenderType.male, image_uuid=None,
            role=RoleType.normal, is_verified=True, is_google_login=False,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_executor: AsyncMock):
        mock_executor.return_value = 1, 'email@email.com', 'nickname', 'MALE', None, 'NORMAL', True, False

        result = await account.read(self.account_id)

        self.assertEqual(result, self.expect_result)

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_not_found(self, mock_executor: AsyncMock):
        mock_executor.return_value = None
        with self.assertRaises(exc.NotFound):
            await account.read(self.account_id)
