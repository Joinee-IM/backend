from unittest.mock import patch
from uuid import UUID

from fastapi import Request
from starlette.responses import RedirectResponse

import app.exceptions as exc
from app.base import do, enums
from app.processor.http import google
from app.utils import Response
from tests import AsyncMock, AsyncTestCase, Mock


class TestGoogleLogin(AsyncTestCase):
    def setUp(self) -> None:
        self.request = Request(scope={'type': 'http'})
        self.role = enums.RoleType.normal

    @patch('app.client.oauth.OAuthHandler.login', AsyncMock(return_value=None))
    async def test_happy_path(self):
        result = await google.google_login(request=self.request, role=self.role)
        self.assertIsNone(result)


class TestAuth(AsyncTestCase):
    def setUp(self) -> None:
        self.role = 'PROVIDER'
        self.request = Request({'type': 'http', 'query_string': {'state': self.role}})
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
        self.read_output = (self.account_id, "mocked_pass_hash", self.role, True)
        self.expect_result = RedirectResponse(url='http://localhost:8000/login')

        self.access_denied_request = Request({'type': 'http', 'query_string': b'access_denied'})

    @patch('app.client.oauth.OAuthHandler.authorize_access_token', new_callable=AsyncMock)
    @patch('app.persistence.database.account.read_by_email', new_callable=AsyncMock)
    @patch('app.persistence.database.account.update_google_token', new_callable=AsyncMock)
    @patch('app.processor.http.google.encode_jwt', new_callable=Mock)
    async def test_happy_path(
        self, mock_encode: Mock, mock_update: AsyncMock,
        mock_read: AsyncMock, mock_authorize: AsyncMock,
    ):
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
    async def test_account_not_found(
        self, mock_encode: Mock, mock_add: AsyncMock,
        mock_read: AsyncMock, mock_authorize: AsyncMock,
    ):
        mock_authorize.return_value = self.google_token
        mock_read.side_effect = exc.NotFound
        mock_add.return_value = self.account_id
        mock_encode.return_value = self.jwt_token

        result = await google.auth(request=self.request)

        mock_authorize.assert_called_with(request=self.request)
        mock_read.assert_called_with(email=self.email)
        mock_add.assert_called_with(
            email=self.email, is_google_login=True,
            nickname=self.email.split("@")[0],
            role=self.role,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
        )
        self.assertIsInstance(result, RedirectResponse)

    async def test_access_denied(self):
        result = await google.auth(request=self.access_denied_request)
        self.assertIsInstance(result, RedirectResponse)


class TestReadFile(AsyncTestCase):
    def setUp(self) -> None:
        self.file_uuid = UUID('262b3702-1891-4e18-958e-82ebe758b0c9')
        self.file = do.GCSFile(
            filename=str(self.file_uuid),
            key=str(self.file_uuid),
            uuid=self.file_uuid,
            bucket='bucket',
        )
        self.url = 'url'
        self.expect_result = Response(data=self.url)

    @patch('app.persistence.database.gcs_file.read', new_callable=AsyncMock)
    @patch('app.persistence.file_storage.gcs.GCSHandler.sign_url', new_callable=AsyncMock)
    async def test_happy_path(self, mock_sign: AsyncMock, mock_read: AsyncMock):
        mock_read.return_value = self.file
        mock_sign.return_value = self.url

        result = await google.read_file(file_uuid=self.file_uuid)

        self.assertEqual(result, self.expect_result)
        mock_read.assert_called_with(
            file_uuid=self.file_uuid,
        )
        mock_sign.assert_called_with(
            filename=self.file.filename,
        )


class TestBatchDownloadFiles(AsyncTestCase):
    def setUp(self) -> None:
        self.data = google.BatchDownloadInput(
            file_uuids=[
                UUID('262b3702-1891-4e18-958e-82ebe758b0c9'),
            ],
        )
        self.sign_url = 'sign_url'
        self.return_data = [
            google.BatchDownloadOutput(
                file_uuid=uuid,
                sign_url=self.sign_url,
            )
            for uuid in self.data.file_uuids
        ]
        self.expect_result = Response(data=self.return_data)

    @patch('app.persistence.file_storage.gcs.GCSHandler.sign_url', new_callable=AsyncMock)
    async def test_happy_path(self, mock_sign: AsyncMock):
        mock_sign.return_value = self.sign_url

        result = await google.batch_download_files(data=self.data)

        self.assertEqual(result, self.expect_result)
