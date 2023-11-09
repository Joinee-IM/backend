from datetime import datetime
from tests import AsyncMock, AsyncTestCase, MockContext
from unittest.mock import patch

import app.exceptions as exc
from app.base import do
from app.base.enums import GenderType, RoleType
from app.processor.http import account
from app.utils.security import AuthedAccount


class TestReadAccount(AsyncTestCase):
    def setUp(self) -> None:
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4))}
        self.wrong_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4))}
        self.account_id = 1
        self.account = do.Account(
            id=1, email='email@email.com', nickname='nickname', gender=GenderType.male, image_uuid=None,
            role=RoleType.normal, is_verified=True, is_google_login=False,
        )
        self.expect_output = account.Response(
            data=self.account,
        )

    @patch('app.processor.http.account.context', new_callable=MockContext)
    @patch('app.persistence.database.account.read', new_callable=AsyncMock)
    async def test_happy_path(self, mock_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read.return_value = self.account

        result = await account.read_account(self.account_id)

        mock_read.assert_called_with(account_id=self.account_id)
        self.assertEqual(result, self.expect_output)
        mock_context.reset_context()

    @patch('app.processor.http.account.context', new_callable=MockContext)
    async def test_no_permission_wrong_account(self, mock_context: MockContext):
        mock_context._context = self.wrong_context
        with self.assertRaises(exc.NoPermission):
            await account.read_account(self.account_id)

        mock_context.reset_context()
