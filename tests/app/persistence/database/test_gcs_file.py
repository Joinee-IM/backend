from unittest.mock import patch
from uuid import UUID

import app.exceptions as exc
from app.base.do import GCSFile
from app.persistence.database import gcs_file
from tests import AsyncMock, AsyncTestCase


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
