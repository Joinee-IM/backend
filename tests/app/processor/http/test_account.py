from datetime import datetime
from unittest.mock import patch
from uuid import UUID

from fastapi import File, UploadFile
from starlette.datastructures import Headers

import app.exceptions as exc
from app.base import do
from app.base.enums import GenderType, RoleType
from app.processor.http import account
from app.utils.security import AuthedAccount
from tests import AsyncMock, AsyncTestCase, Mock, MockContext


class TestReadAccount(AsyncTestCase):
    def setUp(self) -> None:
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4))}
        self.wrong_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4))}
        self.account_id = 1
        self.account = do.Account(
            id=1, email='email@email.com', nickname='nickname', gender=GenderType.male, image_uuid=None,
            role=RoleType.normal, is_verified=True, is_google_login=False,
        )
        self.image_url = 'image_url'
        self.account_output = account.ReadAccountOutput(
            **self.account.model_dump(),
            image_url=None,
        )
        self.expect_output = account.Response(
            data=self.account_output,
        )

    @patch('app.processor.http.account.context', new_callable=MockContext)
    @patch('app.persistence.database.account.read', new_callable=AsyncMock)
    @patch('app.processor.http.account.gcs_handler.sign_url', new_callable=AsyncMock)
    async def test_happy_path(self, mock_sign: AsyncMock, mock_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read.return_value = self.account
        mock_sign.return_value = self.image_url

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


class TestEditAccount(AsyncTestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4))}
        self.wrong_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4))}
        self.happy_path_data = account.EditAccountInput(
            nickname='nickname',
            gender=GenderType.male,
        )
        self.expect_result = account.Response(data=True)

    @patch('app.processor.http.account.context', new_callable=MockContext)
    @patch('app.persistence.database.account.edit', new_callable=AsyncMock)
    async def test_happy_path(self, mock_edit: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context

        result = await account.edit_account(account_id=self.account_id, data=self.happy_path_data)
        self.assertEqual(result, self.expect_result)

        mock_edit.assert_called_with(
            account_id=self.account_id,
            nickname=self.happy_path_data.nickname,
            gender=self.happy_path_data.gender,
        )
        mock_context.reset_context()

    @patch('app.processor.http.account.context', new_callable=MockContext)
    async def test_no_permission(self, mock_context: MockContext):
        mock_context._context = self.wrong_context

        with self.assertRaises(exc.NoPermission):
            await account.edit_account(account_id=self.account_id, data=self.happy_path_data)

        mock_context.reset_context()


class TestUploadAccountImage(AsyncTestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.accept_header = Headers({
            'content-disposition': 'form-data; name="image"; filename="262b3702-1891-4e18-958e-82ebe758b0c9.jpeg"',
            'content-type': 'image/jpeg',
        })
        self.reject_header = Headers({
            'content-disposition': 'form-data; name="image"; filename="262b3702-1891-4e18-958e-82ebe758b0c9.HEIC"',
            'content-type': 'image/heic',
        })

        self.accept_image: UploadFile = UploadFile(File('asdf'), headers=self.accept_header)
        self.reject_image: UploadFile = UploadFile(File('asdf'), headers=self.reject_header)

        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4))}
        self.wrong_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4))}

        self.file_uuid = UUID('262b3702-1891-4e18-958e-82ebe758b0c9')
        self.bucket_name = 'bucket'

        self.expect_result = account.Response(data=True)

    @patch('app.processor.http.account.context', new_callable=MockContext)
    @patch('app.processor.http.account.uuid4', new_callable=Mock)
    @patch('app.persistence.file_storage.avatar.upload', new_callable=AsyncMock)
    @patch('app.persistence.database.gcs_file.add', new_callable=AsyncMock)
    @patch('app.persistence.database.account.edit', new_callable=AsyncMock)
    async def test_happy_path(
        self, mock_edit: AsyncMock, mock_add: AsyncMock,
        mock_upload: AsyncMock, mock_uuid: Mock, mock_context: MockContext,
    ):
        mock_context._context = self.context
        mock_uuid.return_value = self.file_uuid
        mock_upload.return_value = self.file_uuid, self.bucket_name

        result = await account.upload_account_image(account_id=self.account_id, image=self.accept_image)

        self.assertEqual(result, self.expect_result)
        mock_upload.assert_called_with(
            self.accept_image.file,
            file_uuid=self.file_uuid,
            content_type=self.accept_image.content_type,
        )
        mock_add.assert_called_with(
            file_uuid=self.file_uuid, key=str(self.file_uuid),
            bucket=self.bucket_name, filename=str(self.file_uuid),
        )
        mock_edit.assert_called_with(
            account_id=self.account_id,
            image_uuid=self.file_uuid,
        )
        mock_context.reset_context()

    @patch('app.processor.http.account.context', new_callable=MockContext)
    @patch('app.persistence.file_storage.avatar.upload', new_callable=AsyncMock)
    @patch('app.persistence.database.gcs_file.add', new_callable=AsyncMock)
    @patch('app.persistence.database.account.edit', new_callable=AsyncMock)
    async def test_wrong_content_type(
        self, mock_edit: AsyncMock, mock_add: AsyncMock,
        mock_upload: AsyncMock, mock_context: MockContext,
    ):
        mock_context._context = self.context

        mock_upload.return_value = self.file_uuid, self.bucket_name

        with self.assertRaises(exc.IllegalInput):
            await account.upload_account_image(account_id=self.account_id, image=self.reject_image)

        mock_upload.assert_not_called()
        mock_add.assert_not_called()
        mock_edit.assert_not_called()
        mock_context.reset_context()

    @patch('app.processor.http.account.context', new_callable=MockContext)
    @patch('app.persistence.file_storage.avatar.upload', new_callable=AsyncMock)
    @patch('app.persistence.database.gcs_file.add', new_callable=AsyncMock)
    @patch('app.persistence.database.account.edit', new_callable=AsyncMock)
    async def test_no_permission(
        self, mock_edit: AsyncMock, mock_add: AsyncMock,
        mock_upload: AsyncMock, mock_context: MockContext,
    ):
        mock_context._context = self.wrong_context

        with self.assertRaises(exc.NoPermission):
            await account.upload_account_image(account_id=self.account_id, image=self.accept_image)

        mock_upload.assert_not_called()
        mock_add.assert_not_called()
        mock_edit.assert_not_called()
        mock_context.reset_context()


class TestSearchAccount(AsyncTestCase):
    def setUp(self) -> None:
        self.query = 'query'
        self.accounts = [
            do.Account(
                id=1, email='email@email.com', nickname='nickname', gender=GenderType.male, image_uuid=None,
                role=RoleType.normal, is_verified=True, is_google_login=False,
            ),
        ]
        self.expect_result = account.Response(
            data=self.accounts,
        )

    @patch('app.persistence.database.account.search', new_callable=AsyncMock)
    async def test_happy_path(self, mock_search: AsyncMock):
        mock_search.return_value = self.accounts

        result = await account.search_account(query=self.query)

        self.assertEqual(result, self.expect_result)
        mock_search.assert_called_with(
            query=self.query,
        )


class TestEditPassword(AsyncTestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=self.account_id, time=datetime(2023, 11, 4))}
        self.wrong_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4))}
        self.data = account.EditPasswordInput(
            old_password='old',
            new_password='new',
        )
        self.account = do.Account(
            id=1, email='email@email.com', nickname='nickname', gender=GenderType.male, image_uuid=None,
            role=RoleType.normal, is_verified=True, is_google_login=False,
        )
        self.pass_hash = 'pass_hash'
        self.expect_result = account.Response()

    @patch('app.processor.http.account.context', new_callable=MockContext)
    @patch('app.persistence.database.account.read', new_callable=AsyncMock)
    @patch('app.persistence.database.account.read_by_email', new_callable=AsyncMock)
    @patch('app.processor.http.account.security.verify_password', new_callable=Mock)
    @patch('app.processor.http.account.security.hash_password', new_callable=Mock)
    @patch('app.persistence.database.account.edit', new_callable=AsyncMock)
    async def test_happy_path(self, mock_edit: AsyncMock, mock_hash: Mock, mock_verify: Mock,
                              mock_read_by_email: AsyncMock, mock_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read.return_value = self.account
        mock_read_by_email.return_value = None, self.pass_hash, None, None
        mock_verify.return_value = True
        mock_hash.return_value = self.pass_hash

        result = await account.edit_password(account_id=self.account_id, data=self.data)

        self.assertEqual(result, self.expect_result)
        mock_edit.assert_called_with(
            account_id=self.account_id,
            pass_hash=self.pass_hash,
        )
        mock_context.reset_context()

    @patch('app.processor.http.account.context', new_callable=MockContext)
    @patch('app.persistence.database.account.read', new_callable=AsyncMock)
    @patch('app.persistence.database.account.read_by_email', new_callable=AsyncMock)
    @patch('app.processor.http.account.security.verify_password', new_callable=Mock)
    async def test_wrong_password(self, mock_verify: Mock, mock_read_by_email: AsyncMock,
                                  mock_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read.return_value = self.account
        mock_read_by_email.return_value = None, self.pass_hash, None, None
        mock_verify.return_value = False

        with self.assertRaises(exc.WrongPassword):
            await account.edit_password(account_id=self.account_id, data=self.data)

        mock_context.reset_context()

    @patch('app.processor.http.account.context', new_callable=MockContext)
    async def test_no_permission(self, mock_context: MockContext):
        mock_context._context = self.wrong_context

        with self.assertRaises(exc.NoPermission):
            await account.edit_password(account_id=self.account_id, data=self.data)

        mock_context.reset_context()
