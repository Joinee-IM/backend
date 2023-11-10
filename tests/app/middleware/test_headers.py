from datetime import datetime
from unittest.mock import patch

from app.middleware.headers import get_auth_token
from app.utils.security import AuthedAccount
from tests import AsyncTestCase, Mock, MockContext


class TestGetAuthToken(AsyncTestCase):
    def setUp(self) -> None:
        self.context = {
            'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4)),
            'REQUEST_TIME': datetime(2023, 11, 4)
        }
        self.auth_token = 'token'
        self.auth_account = AuthedAccount(id=1, time=datetime(2023, 10, 10))

    @patch('app.middleware.headers.context', new_callable=MockContext)
    @patch('app.middleware.headers.security.decode_jwt', new_callable=Mock)
    async def test_happy_path(self, mock_decode: Mock, mock_context: MockContext):
        mock_decode.return_value = self.auth_account
        mock_context._context = self.context

        await get_auth_token(self.auth_token)

        mock_decode.assert_called_with(
            self.auth_token,
            self.context['REQUEST_TIME'],
        )
        self.assertEqual(mock_context.account, self.auth_account)

    @patch('app.middleware.headers.context', new_callable=MockContext)
    @patch('app.middleware.headers.security.decode_jwt', new_callable=Mock)
    async def test_no_token(self, mock_decode: Mock, mock_context: MockContext):
        mock_decode.return_value = self.auth_account
        mock_context._context = self.context

        await get_auth_token(None)  # noqa

        mock_decode.assert_not_called()
        self.assertEqual(mock_context.get_account(), None)
