from unittest.mock import patch
from uuid import UUID

import app.exceptions as exc
from app.base import do
from app.base.enums import GenderType, RoleType
from app.persistence.database import account
from tests import AsyncMock, AsyncTestCase, Mock


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

    @patch(
        'app.persistence.database.util.PostgresQueryExecutor.execute',
        AsyncMock(side_effect=exc.UniqueViolationError),
    )
    async def test_add_account_unique_error(self):
        with self.assertRaises(exc.UniqueViolationError):
            await account.add(
                email='email@email.com', pass_hash='pass_hash', nickname='nickname',
                gender=GenderType.unrevealed, role=RoleType.normal, is_google_login=False,
            )


class TestReadByEmail(AsyncTestCase):
    def setUp(self) -> None:
        self.email = 'email'
        self.execute_result = 1, 'hash', 'NORMAL', True
        self.execute_result_not_verified = 1, 'hash', 'NORMAL', False
        self.expect_output = 1, 'hash', RoleType.normal, True

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


class TestUpdateGoogleToken(AsyncTestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.access_token = 'access'
        self.refresh_token = 'refresh'

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', AsyncMock(return_value=None))
    async def test_happy_path(self):
        result = await account.update_google_token(
            account_id=self.account_id,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
        )
        self.assertIsNone(result)


class TestEdit(AsyncTestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.nickname = 'nickname'
        self.gender = GenderType.male
        self.image_uuid = UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c')

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', AsyncMock())
    async def test_happy_path(self, mock_init: Mock):
        result = await account.edit(
            account_id=self.account_id,
            nickname=self.nickname,
            gender=self.gender,
            image_uuid=self.image_uuid,
        )
        self.assertIsNone(result)

        mock_init.assert_called_with(
            sql='UPDATE account'
                '   SET nickname = %(nickname)s, gender = %(gender)s, image_uuid = %(image_uuid)s'
                ' WHERE id = %(account_id)s',
            account_id=self.account_id, nickname=self.nickname, gender=self.gender, image_uuid=self.image_uuid,
            fetch=None,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', AsyncMock())
    async def test_only_edit_one(self, mock_init: Mock):
        result = await account.edit(
            account_id=self.account_id,
            nickname=self.nickname,
            gender=None,
        )
        self.assertIsNone(result)

        mock_init.assert_called_with(
            sql='UPDATE account'
                '   SET nickname = %(nickname)s'
                ' WHERE id = %(account_id)s',
            account_id=self.account_id, nickname=self.nickname, fetch=None,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', AsyncMock())
    async def test_no_edit(self, mock_init: Mock):
        result = await account.edit(
            account_id=self.account_id,
            nickname=None,
            gender=None,
        )
        self.assertIsNone(result)

        mock_init.assert_not_called()


class TestSearch(AsyncTestCase):
    def setUp(self) -> None:
        self.query = 'query'
        self.raw_accounts = [
            (1, 'email@email.com', 'nickname', 'MALE', None, 'NORMAL', True, False),
        ]
        self.accounts = [
            do.Account(
                id=1, email='email@email.com', nickname='nickname', gender=GenderType.male, image_uuid=None,
                role=RoleType.normal, is_verified=True, is_google_login=False,
            ),
        ]

    async def test_happy_path(self):
        pass
