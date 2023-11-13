from unittest.mock import patch

from fastapi import Request

from app.client.oauth import OAuthHandler
from app.config import GoogleConfig
from tests import AsyncMock, AsyncTestCase, Mock


class MockGoogleConfig(GoogleConfig):
    def __init__(self):
        self.CLIENT_ID = 'client_id'
        self.CLIENT_SECRET = 'client_secret'
        self.LOGIN_REDIRECT_URI = 'login_redirect_uri'
        self.SERVER_URL = 'server_url'
        self.CLIENT_KWARGS = 'client_kwargs'


class TestOAuthHandler(AsyncTestCase):
    def setUp(self) -> None:
        self.oauth_handler = OAuthHandler()
        self.google_config = MockGoogleConfig()
        self.request = Request({
            'type': 'http',
            'method': 'GET',
            'headers': [],
        })

    @patch('app.client.oauth.OAuth', new_callable=Mock)
    def test_initialize(self, mock_oauth: Mock):
        mock_register = Mock()
        mock_oauth.return_value = mock_register

        result = self.oauth_handler.initialize(google_config=self.google_config)
        self.assertIsNone(result)
        self.assertEqual(self.oauth_handler.login_redirect_url, self.google_config.LOGIN_REDIRECT_URI)

    @patch('app.client.oauth.OAuth', new_callable=Mock)
    async def test_login(self, mock_oauth: Mock):
        mock_oauth_return = AsyncMock()
        mock_oauth.return_value = mock_oauth_return

        oauth_handler = OAuthHandler()
        oauth_handler.initialize(self.google_config)
        await oauth_handler.login(self.request)

    @patch('app.client.oauth.OAuth', new_callable=Mock)
    async def test_authorize(self, mock_oauth: Mock):
        mock_oauth_return = AsyncMock()
        mock_oauth.return_value = mock_oauth_return

        oauth_handler = OAuthHandler()
        oauth_handler.initialize(self.google_config)
        await oauth_handler.authorize_access_token(self.request)
