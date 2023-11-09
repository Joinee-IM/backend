from tests import AsyncMock, AsyncTestCase, Mock
from unittest.mock import patch
from uuid import UUID

from fastapi import Response as FastAPIResponse

import app.processor
from app import exceptions as exc
from app.base.enums import GenderType, RoleType
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
            email='email@email.com',
            password='password',
        )
        self.response = FastAPIResponse()
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

        result = await public.login(data=self.login_input, response=self.response)

        mock_read.assert_called_with(email=self.login_input.email)
        mock_verify.assert_called_with(
            self.login_input.password, self.pass_hash
        )
        mock_encode.assert_called_with(
            account_id=self.account_id,
        )

        self.assertEqual(result, Response(data=self.expect_output))

    @patch('app.persistence.database.account.read_by_email', new_callable=AsyncMock)
    async def test_no_account(self, mock_read: AsyncMock):
        mock_read.side_effect = TypeError
        with self.assertRaises(exc.LoginFailed):
            await public.login(self.login_input, self.response)

        mock_read.assert_called_with(email=self.login_input.email)

    @patch('app.persistence.database.account.read_by_email', new_callable=AsyncMock)
    @patch('app.processor.http.public.verify_password', new_callable=Mock)
    async def test_wrong_password(self, mock_verify: Mock, mock_read: AsyncMock):
        mock_read.return_value = (self.account_id, self.pass_hash, self.role)
        mock_verify.return_value = False

        with self.assertRaises(exc.LoginFailed):
            await public.login(self.login_input, self.response)

        mock_read.assert_called_with(email=self.login_input.email)
        mock_verify.assert_called_with(
            self.login_input.password, self.pass_hash
        )


class TestEmailVerification(AsyncTestCase):
    def setUp(self) -> None:
        self.code = UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c')
        self.expect_output = Response(data=public.EmailVerificationOutput(success=True))

    @patch('app.persistence.database.email_verification.verify_email', new_callable=AsyncMock)
    async def test_happy_path(self, mock_verify: AsyncMock):
        result = await public.email_verification(code=self.code)

        mock_verify.assert_called_with(code=self.code)
        self.assertEqual(result, self.expect_output)


class TestAddAccount(AsyncTestCase):
    def setUp(self) -> None:
        self.data = app.processor.http.public.AddAccountInput(
            email='email@email.com',
            password='password',
            nickname='nickname',
            gender=GenderType.male,
            role=RoleType.normal,
        )
        self.account_id = 1
        self.hashed_password = 'hash'
        self.code = UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c')
        self.expect_output = Response(data=app.processor.http.public.AddAccountOutput(id=self.account_id))

    @patch('app.persistence.database.account.add', new_callable=AsyncMock)
    @patch('app.processor.http.public.hash_password', new_callable=Mock)
    @patch('app.persistence.database.email_verification.add', new_callable=AsyncMock)
    @patch('app.persistence.email.verification.send', new_callable=AsyncMock)
    async def test_happy_path(self, mock_send: AsyncMock,
                              mock_add_verification: AsyncMock,
                              mock_hash: Mock,
                              mock_add_account: AsyncMock):
        mock_hash.return_value = self.hashed_password
        mock_add_account.return_value = self.account_id
        mock_add_verification.return_value = self.code

        result = await app.processor.http.public.add_account(data=self.data)

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
    @patch('app.processor.http.public.hash_password', new_callable=Mock)
    async def test_email_exists(self, mock_hash: Mock, mock_add_account: AsyncMock):
        mock_hash.return_value = self.hashed_password
        mock_add_account.side_effect = exc.UniqueViolationError

        with self.assertRaises(exc.EmailExists):
            await app.processor.http.public.add_account(data=self.data)

        mock_hash.assert_called_with(self.data.password)
        mock_add_account.assert_called_with(
            email=self.data.email,
            pass_hash=self.hashed_password,
            nickname=self.data.nickname,
            gender=self.data.gender,
            role=self.data.role,
            is_google_login=False,
        )


class TestResendEmailVerification(AsyncTestCase):
    def setUp(self) -> None:
        self.email = 'email@email.com'
        self.data = public.ResendEmailVerificationInput(email=self.email)
        self.account_id = 1
        self.code = UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c')
        self.expect_output = Response(data=public.EmailVerificationOutput())

    @patch('app.persistence.database.account.read_by_email', new_callable=AsyncMock)
    @patch('app.persistence.database.email_verification.read', new_callable=AsyncMock)
    @patch('app.persistence.email.verification.send', new_callable=AsyncMock)
    async def test_happy_path(self, mock_send: AsyncMock,
                              mock_read_verification: AsyncMock,
                              mock_read_by_email: AsyncMock):
        mock_read_by_email.return_value = self.account_id,
        mock_read_verification.return_value = self.code

        result = await public.resend_email_verification(data=self.data)

        self.assertEqual(result, self.expect_output)
        mock_read_by_email.assert_called_with(email=self.email)
        mock_read_verification.assert_called_with(account_id=self.account_id, email=self.email)
        mock_send.assert_called_with(to=self.email, code=str(self.code))


class TestForgetPassword(AsyncTestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.code = UUID('d0a7fb2d-dca7-4e1e-85a0-f0f5f6f0c651')
        self.email = 'email@email.com'

        self.data = public.ForgetPasswordInput(email=self.email)
        self.expect_result = Response()

    @patch('app.persistence.database.account.read_by_email', new_callable=AsyncMock)
    @patch('app.persistence.database.email_verification.add', new_callable=AsyncMock)
    @patch('app.persistence.email.forget_password.send', new_callable=AsyncMock)
    async def test_happy_path(self, mock_send: AsyncMock, mock_add: AsyncMock, mock_read: AsyncMock):
        mock_read.return_value = self.account_id,
        mock_add.return_value = self.code

        result = await public.forget_password(data=self.data)

        self.assertEqual(result, self.expect_result)
        mock_read.assert_called_with(email=self.data.email)
        mock_add.assert_called_with(account_id=self.account_id, email=self.data.email)
        mock_send.assert_called_with(to=self.data.email, code=str(self.code))


class TestResetPassword(AsyncTestCase):
    def setUp(self) -> None:
        self.code = 'd0a7fb2d-dca7-4e1e-85a0-f0f5f6f0c651'
        self.password = 'password'
        self.hashed = 'psd'
        self.data = public.ResetPasswordInput(code=self.code, password=self.password)
        self.expect_result = Response()

    @patch('app.persistence.database.account.reset_password', new_callable=AsyncMock)
    @patch('app.processor.http.public.hash_password', new_callable=Mock)
    async def test_happy_path(self, mock_hash: Mock, mock_reset: AsyncMock):
        mock_hash.return_value = self.hashed

        result = await public.reset_password(data=self.data)

        self.assertEqual(result, self.expect_result)
        mock_hash.assert_called_with(self.data.password)
        mock_reset.assert_called_with(code=self.data.code, pass_hash=self.hashed)
