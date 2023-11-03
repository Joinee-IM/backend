from test import AsyncMock, AsyncTestCase, Mock
from unittest.mock import patch
from uuid import UUID

import app.exceptions as exc
from app.base.enums import GenderType, RoleType
from app.processor.http import account
from app.utils import Response


class TestAddAccount(AsyncTestCase):
    def setUp(self) -> None:
        self.data = account.AddAccountInput(
            email='email',
            password='password',
            nickname='nickname',
            gender=GenderType.male,
            role=RoleType.normal,
        )
        self.account_id = 1
        self.hashed_password = 'hash'
        self.code = UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c')
        self.expect_output = Response(data=account.AddAccountOutput(id=self.account_id))

    @patch('app.persistence.database.account.add', new_callable=AsyncMock)
    @patch('app.processor.http.account.hash_password', new_callable=Mock)
    @patch('app.persistence.database.email_verification.add', new_callable=AsyncMock)
    @patch('app.persistence.email.verification.send', new_callable=AsyncMock)
    async def test_happy_path(self, mock_send: AsyncMock,
                              mock_add_verification: AsyncMock,
                              mock_hash: Mock,
                              mock_add_account: AsyncMock):
        mock_hash.return_value = self.hashed_password
        mock_add_account.return_value = self.account_id
        mock_add_verification.return_value = self.code

        result = await account.add_account(data=self.data)

        self.assertEqual(result, self.expect_output)
        mock_hash.assert_called_with(self.data.password)
        mock_add_account.assert_called_with(
            email=self.data.email,
            pass_hash=self.hashed_password,
            nickname=self.data.nickname,
            gender=self.data.gender,
            role=self.data.role,
            is_google_login=False,
        )
        mock_add_verification.assert_called_with(account_id=self.account_id, email=self.data.email)
        mock_send.assert_called_with(to=self.data.email, code=str(self.code))

    @patch('app.persistence.database.account.add', new_callable=AsyncMock)
    @patch('app.processor.http.account.hash_password', new_callable=Mock)
    async def test_email_exists(self, mock_hash: Mock, mock_add_account: AsyncMock):
        mock_hash.return_value = self.hashed_password
        mock_add_account.side_effect = exc.UniqueViolationError

        with self.assertRaises(exc.EmailExists):
            await account.add_account(data=self.data)

        mock_hash.assert_called_with(self.data.password)
        mock_add_account.assert_called_with(
            email=self.data.email,
            pass_hash=self.hashed_password,
            nickname=self.data.nickname,
            gender=self.data.gender,
            role=self.data.role,
            is_google_login=False,
        )
