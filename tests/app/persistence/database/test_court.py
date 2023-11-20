from unittest.mock import patch

import app.exceptions as exc
from app.base import do
from app.persistence.database import court
from tests import AsyncMock, AsyncTestCase, Mock


class TestRead(AsyncTestCase):
    def setUp(self) -> None:
        self.raw_court = 1, 1
        self.court_id = 1
        self.court = do.Court(id=1, venue_id=1)

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_read(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = self.raw_court

        result = await court.read(court_id=self.court_id)

        self.assertEqual(result, self.court)
        mock_init.assert_called_with(
            sql='SELECT id, venue_id'
                '  FROM court'
                ' WHERE id = %(court_id)s',
            court_id=self.court_id, fetch=1,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_not_founc(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = None

        with self.assertRaises(exc.NotFound):
            await court.read(court_id=self.court_id)

        mock_init.assert_called_with(
            sql='SELECT id, venue_id'
                '  FROM court'
                ' WHERE id = %(court_id)s',
            court_id=self.court_id, fetch=1,
        )
