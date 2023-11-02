from test import AsyncMock, AsyncTestCase, Mock
from unittest.mock import patch

from app import exceptions as exc
from app.base.enums import RoleType
from app.processor.http import public
from app.utils import Response


class TestDefaultPage(AsyncTestCase):
    def setUp(self) -> None:
        self.expect_result = '<a href="/docs">/docs</a>'

    async def test_happy_path(self):
        result = await public.default_page()
        self.assertEqual(result, self.expect_result)


class TestHealthCheck(AsyncTestCase):
    def setUp(self) -> None:
        self.expect_result = Response(data=public.HealthCheckOutput())

    async def test_happy_path(self):
        result = await public.health_check()
        self.assertEqual(result.data.health, self.expect_result.data.health)


class TestLogin(AsyncTestCase):
    def setUp(self) -> None:
        self.login_input = public.LoginInput(
            email='email',
            password='password',
        )
        self.pass_hash = 'pass_hash'
        self.account_id = 1
        self.role = RoleType.normal
        self.expect_output = public.LoginOutput(
            account_id=self.account_id,
            token='token'
        )

    @patch('app.persistence.database.account.read_by_email', new_callable=AsyncMock)
    @patch('app.processor.http.public.verify_password', new_callable=Mock)
    @patch('app.processor.http.public.encode_jwt', new_callable=Mock)
    async def test_happy_path(self, mock_encode: Mock, mock_verify: Mock, mock_read: AsyncMock):
        mock_read.return_value = (self.account_id, self.pass_hash, self.role)
        mock_verify.return_value = True
        mock_encode.return_value = 'token'

        result = await public.login(self.login_input)

        mock_read.assert_called_with(email=self.login_input.email)
        mock_verify.assert_called_with(
            self.login_input.password, self.pass_hash
        )
        mock_encode.assert_called_with(
            account_id=self.account_id, role=self.role
        )

        self.assertEqual(result, Response(data=self.expect_output))

    @patch('app.persistence.database.account.read_by_email', new_callable=AsyncMock)
    async def test_no_account(self, mock_read: AsyncMock):
        mock_read.side_effect = TypeError
        with self.assertRaises(exc.LoginFailed):
            await public.login(self.login_input)

        mock_read.assert_called_with(email=self.login_input.email)

    @patch('app.persistence.database.account.read_by_email', new_callable=AsyncMock)
    @patch('app.processor.http.public.verify_password', new_callable=Mock)
    async def test_wrong_password(self, mock_verify: Mock, mock_read: AsyncMock):
        mock_read.return_value = (self.account_id, self.pass_hash, self.role)
        mock_verify.return_value = False

        with self.assertRaises(exc.LoginFailed):
            await public.login(self.login_input)

        mock_read.assert_called_with(email=self.login_input.email)
        mock_verify.assert_called_with(
            self.login_input.password, self.pass_hash
        )
