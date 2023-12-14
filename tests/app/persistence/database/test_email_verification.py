from unittest.mock import patch
from uuid import UUID

import app.exceptions as exc
from app.persistence.database import email_verification
from tests import AsyncMock, AsyncTestCase


class TestAdd(AsyncTestCase):
    def setUp(self) -> None:
        self.uuid = UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c')
        self.account_id = 1
        self.email = 'abc@email.com'

    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock):
        mock_fetch.return_value = self.uuid,
        result = await email_verification.add(account_id=self.account_id, email=self.email)

        self.assertEqual(result, self.uuid)


class TestVerifyEmail(AsyncTestCase):
    def setUp(self) -> None:
        self.code = UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c')
        self.account_id = 1

    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock, mock_fetch: AsyncMock):
        mock_fetch.return_value = self.account_id,
        mock_execute.return_value = None

        result = await email_verification.verify_email(self.code)

        self.assertIsNone(result)

    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_not_found(self, mock_fetch: AsyncMock):
        mock_fetch.return_value = None

        with self.assertRaises(exc.NotFound):
            await email_verification.verify_email(self.code)


class TestRead(AsyncTestCase):
    def setUp(self) -> None:
        self.email = 'email'
        self.account_id = 1
        self.code = UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c')

    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_executor: AsyncMock):
        mock_executor.return_value = self.code,
        result = await email_verification.read(account_id=self.account_id, email=self.email)

        self.assertEqual(result, self.code)

    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_not_found(self, mock_executor: AsyncMock):
        mock_executor.return_value = None
        with self.assertRaises(exc.NotFound):
            await email_verification.read(account_id=self.account_id, email=self.email)
