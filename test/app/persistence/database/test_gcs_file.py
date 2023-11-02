from unittest.mock import patch
from uuid import UUID

from app.persistence.database import gcs_file
from app.base.do import GCSFile
from test import AsyncMock, AsyncTestCase


class TestAdd(AsyncTestCase):
    def setUp(self) -> None:
        self.gcs_file = GCSFile(
            uuid=UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c'),
            key='fad08f83-6ad7-429f-baa6-b1c3abf4991c',
            bucket='bucket',
            filename='filename'
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', AsyncMock(return_value=None))
    @patch('app.log.context', AsyncTestCase.context)
    async def test_happy_path(self):
        await gcs_file.add(self.gcs_file)
