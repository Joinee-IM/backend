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


class TestBrowse(AsyncTestCase):
    def setUp(self) -> None:
        self.venue_id = 1
        self.raw_court = [
            (1, 1),
            (2, 1),
        ]
        self.courts = [
            do.Court(
                id=1,
                venue_id=1,
            ),
            do.Court(
                id=2,
                venue_id=1,
            ),
        ]

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_court

        result = await court.browse(venue_id=self.venue_id)

        self.assertEqual(result, self.courts)
        mock_init.assert_called_with(
            sql='SELECT id, venue_id'
                '  FROM court'
                ' WHERE venue_id = %(venue_id)s',
            venue_id=self.venue_id, fetch='all',
        )
