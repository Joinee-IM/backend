from unittest.mock import patch

from app.config import ServiceConfig, SMTPConfig
from app.persistence import email
from tests import AsyncMock, AsyncTestCase


class MockSMTPConfig(SMTPConfig):
    def __init__(self):
        self.host = 'host'
        self.port = 'port'
        self.username = 'username'
        self.password = 'password'
        self.use_tls = True


class MockServiceConfig(ServiceConfig):
    def __init__(self):
        self.domain = 'domain'
        self.port = 'port'
        self.use_https = True


class TestSend(AsyncTestCase):
    async def asyncSetUp(self) -> None:
        self.to = 'to@to.com'
        self.code = 'code'
        self.smtp_handler = email.SMTPHandler()
        self.smtp_config = MockSMTPConfig()
        self.service_config = MockServiceConfig()

        await self.smtp_handler.initialize(smtp_config=self.smtp_config)

    @patch('app.persistence.email.SMTPHandler.send_message', new_callable=AsyncMock)
    @patch('app.persistence.email.forget_password.service_config', MockServiceConfig())
    async def test_happy_path(self, mock_send: AsyncMock):
        await email.invitation.send(to=self.to, meet_code=self.code)
        mock_send.assert_called_once()
