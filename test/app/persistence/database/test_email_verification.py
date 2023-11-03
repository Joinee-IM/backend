from test import AsyncMock, AsyncTestCase
from unittest.mock import patch
from uuid import UUID

import app.exceptions as exc
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


class TestVerifyEmail(AsyncTestCase):
    def setUp(self) -> None:
        self.code = UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c')
        self.account_id = 1

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute2: AsyncMock, mock_execute1: AsyncMock):
        mock_execute1.return_value = self.account_id,
        mock_execute2.return_value = None

        result = await email_verification.verify_email(self.code)

        self.assertIsNone(result)

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_not_found(self, mock_execute: AsyncMock):
        mock_execute.return_value = None

        with self.assertRaises(exc.NotFound):
            await email_verification.verify_email(self.code)
