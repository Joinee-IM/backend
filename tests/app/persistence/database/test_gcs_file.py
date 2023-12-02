from unittest.mock import patch
from uuid import UUID

import app.exceptions as exc
from app.base.do import GCSFile
from app.const import BUCKET_NAME
from app.persistence.database import gcs_file
from tests import AsyncMock, AsyncTestCase, Mock


class TestAddWithDo(AsyncTestCase):
    def setUp(self) -> None:
        self.gcs_file = GCSFile(
            uuid=UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c'),
            key='fad08f83-6ad7-429f-baa6-b1c3abf4991c',
            bucket='bucket',
            filename='filename',
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', AsyncMock(return_value=None))
    @patch('app.log.context', AsyncTestCase.context)
    async def test_happy_path(self):
        await gcs_file.add_with_do(self.gcs_file)


class TestAdd(AsyncTestCase):
    def setUp(self) -> None:
        self.file_uuid = UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c')
        self.key = str(self.file_uuid)
        self.bucket = 'bucket'
        self.filename = str(self.file_uuid)

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', AsyncMock())
    async def test_happy_path(self):
        result = await gcs_file.add(
            file_uuid=self.file_uuid,
            key=self.key,
            bucket=self.bucket,
            filename=self.filename,
        )
        self.assertIsNone(result)


class TestRead(AsyncTestCase):
    def setUp(self) -> None:
        self.file_uuid = UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c')
        self.key = str(self.file_uuid)
        self.bucket = 'bucket'
        self.filename = str(self.file_uuid)

        self.expect_result = GCSFile(
            uuid=UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c'),
            key='fad08f83-6ad7-429f-baa6-b1c3abf4991c',
            bucket='bucket',
            filename='fad08f83-6ad7-429f-baa6-b1c3abf4991c',
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock):
        mock_fetch.return_value = self.file_uuid, self.key, self.bucket, self.filename

        result = await gcs_file.read(file_uuid=self.file_uuid)

        self.assertEqual(result, self.expect_result)

    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_not_found(self, mock_fetch: AsyncMock):
        mock_fetch.return_value = None

        with self.assertRaises(exc.NotFound):
            await gcs_file.read(file_uuid=self.file_uuid)


class TestBatchAddWithDo(AsyncTestCase):
    def setUp(self) -> None:
        self.gcs_files = [
            GCSFile(
                uuid=UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c'),
                key='fad08f83-6ad7-429f-baa6-b1c3abf4991c',
                bucket='bucket',
                filename='fad08f83-6ad7-429f-baa6-b1c3abf4991c',
            ),
            GCSFile(
                uuid=UUID('04321607-1b70-47c4-906a-d4b8f3ef8bcb'),
                key='04321607-1b70-47c4-906a-d4b8f3ef8bcb',
                bucket='bucket',
                filename='04321607-1b70-47c4-906a-d4b8f3ef8bcb',
            ),
        ]
        self.params = {
            'file_uuid_0': UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c'),
            'file_uuid_1': UUID('04321607-1b70-47c4-906a-d4b8f3ef8bcb'),
            'key_0': 'fad08f83-6ad7-429f-baa6-b1c3abf4991c',
            'key_1': '04321607-1b70-47c4-906a-d4b8f3ef8bcb',
            'filename_0': 'fad08f83-6ad7-429f-baa6-b1c3abf4991c',
            'filename_1': '04321607-1b70-47c4-906a-d4b8f3ef8bcb',
        }
        self.bucket_name = BUCKET_NAME

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = None

        result = await gcs_file.batch_add_with_do(
            gcs_files=self.gcs_files,
        )

        self.assertIsNone(result)

        mock_init.assert_called_with(
            sql=r'INSERT INTO gcs_file'
                r'            (file_uuid, key, bucket, filename)'
                r'     VALUES (%(file_uuid_0)s, %(key_0)s, %(bucket)s, %(filename_0)s),'
                r' (%(file_uuid_1)s, %(key_1)s, %(bucket)s, %(filename_1)s)',
            bucket=BUCKET_NAME, **self.params,
        )
