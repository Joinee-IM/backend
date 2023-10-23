from unittest.mock import patch
from uuid import UUID

from app.persistence.database import s3_file
from app.base.do import S3File
from test import AsyncMock, AsyncTestCase


class TestAdd(AsyncTestCase):
    def setUp(self) -> None:
        self.s3_file = S3File(
            uuid=UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c'),
            key='fad08f83-6ad7-429f-baa6-b1c3abf4991c',
            bucket='bucket',
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', AsyncMock(return_value=None))
    @patch('app.log.context', AsyncTestCase.context)
    async def test_happy_path(self):
        await s3_file.add(self.s3_file)
