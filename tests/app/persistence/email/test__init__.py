from unittest.mock import patch

from app.config import SMTPConfig
from app.persistence import email
from tests import AsyncMock, AsyncTestCase


class MockSMTPConfig(SMTPConfig):
    def __init__(self):
        self.host = 'host'
        self.port = 'port'
        self.username = 'username'
        self.password = 'password'
        self.use_tls = True


class TestSMTPHandler(AsyncTestCase):
    @patch('aiosmtplib.SMTP', new_callable=AsyncMock)
    async def test_initialize(self, mock_smtp: AsyncMock):
        smtp_handler = email.SMTPHandler()
        smtp_handler._client = None
        smtp_config = MockSMTPConfig()
        await smtp_handler.initialize(smtp_config=smtp_config)

        mock_smtp.assert_called_with(
            hostname='host',
            port='port',
            username='username',
            password='password',
            use_tls=True,
        )

    @patch('aiosmtplib.SMTP', new_callable=AsyncMock)
    async def test_already_have_client(self, mock_smtp: AsyncMock):
        smtp_handler = email.SMTPHandler()
        smtp_config = MockSMTPConfig()
        smtp_handler._client = 1
        await smtp_handler.initialize(smtp_config=smtp_config)

        mock_smtp.assert_not_called()
