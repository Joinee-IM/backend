from test import AsyncMock, AsyncTestCase
from unittest.mock import patch
from uuid import UUID

from app.persistence.database import email_verification


class TestAdd(AsyncTestCase):
    def setUp(self) -> None:
        self.uuid = UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c')
        self.account_id = 1
        self.email = 'abc@email.com'

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock):
        mock_execute.return_value = self.uuid,
        result = await email_verification.add(account_id=self.account_id, email=self.email)

        self.assertEqual(result, self.uuid)
