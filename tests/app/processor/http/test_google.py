from tests import AsyncMock, AsyncTestCase, Mock
from unittest.mock import patch

from fastapi import Request
from starlette.responses import RedirectResponse

import app.exceptions as exc
from app.processor.http import google


class TestGoogleLogin(AsyncTestCase):
    def setUp(self) -> None:
        self.request = Request(scope={'type': 'http'})

    @patch('app.client.oauth.OAuthHandler.login', AsyncMock(return_value=None))
    async def test_happy_path(self):
        result = await google.google_login(request=self.request)
        self.assertIsNone(result)


class TestAuth(AsyncTestCase):
    def setUp(self) -> None:
        self.request = Request({'type': 'http', 'query_string': b''})
        self.email = 'user@user.com'
        self.access_token = 'access_token'
        self.refresh_token = 'refresh_token'
        self.google_token = {
            'userinfo': {'email': self.email},
            'access_token': 'access_token',
            'refresh_token': 'refresh_token',
        }
        self.jwt_token = 'jwt'
        self.account_id = 1
        self.read_output = self.account_id,
        self.expect_result = RedirectResponse(url='http://localhost:8000/login')

        self.access_denied_request = Request({'type': 'http', 'query_string': b'access_denied'})

    @patch('app.client.oauth.OAuthHandler.authorize_access_token', new_callable=AsyncMock)
    @patch('app.persistence.database.account.read_by_email', new_callable=AsyncMock)
    @patch('app.persistence.database.account.update_google_token', new_callable=AsyncMock)
    @patch('app.processor.http.google.encode_jwt', new_callable=Mock)
    async def test_happy_path(self, mock_encode: Mock, mock_update: AsyncMock,
                              mock_read: AsyncMock, mock_authorize: AsyncMock):
        mock_authorize.return_value = self.google_token
        mock_read.return_value = self.read_output
        mock_update.return_value = None
        mock_encode.return_value = self.jwt_token

        result = await google.auth(request=self.request)

        mock_authorize.assert_called_with(request=self.request)
        mock_read.assert_called_with(email=self.email)
        mock_update.assert_called_with(
            account_id=self.account_id,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
        )
        self.assertIsInstance(result, RedirectResponse)

    @patch('app.client.oauth.OAuthHandler.authorize_access_token', new_callable=AsyncMock)
    @patch('app.persistence.database.account.read_by_email', new_callable=AsyncMock)
    @patch('app.persistence.database.account.add', new_callable=AsyncMock)
    @patch('app.processor.http.google.encode_jwt', new_callable=Mock)
    async def test_account_not_found(self, mock_encode: Mock, mock_add: AsyncMock,
                                     mock_read: AsyncMock, mock_authorize: AsyncMock):
        mock_authorize.return_value = self.google_token
        mock_read.side_effect = exc.NotFound
        mock_add.return_value = self.account_id
        mock_encode.return_value = self.jwt_token

        result = await google.auth(request=self.request)

        mock_authorize.assert_called_with(request=self.request)
        mock_read.assert_called_with(email=self.email)
        mock_add.assert_called_with(
            email=self.email, is_google_login=True,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
        )
        self.assertIsInstance(result, RedirectResponse)

    async def test_access_denied(self):
        result = await google.auth(request=self.access_denied_request)
        self.assertIsInstance(result, RedirectResponse)
