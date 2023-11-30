from unittest.mock import patch

import app.exceptions as exc
from app.base import do
from app.persistence.database import court
from tests import AsyncMock, AsyncTestCase, Mock


class TestRead(AsyncTestCase):
    def setUp(self) -> None:
        self.raw_court = 1, 1, 1, True
        self.court_id = 1
        self.court = do.Court(id=1, venue_id=1, is_published=True, number=1)

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_read(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_court

        result = await court.read(court_id=self.court_id)

        self.assertEqual(result, self.court)
        mock_init.assert_called_with(
            sql='SELECT id, venue_id, number, is_published'
                '  FROM court'
                ' WHERE id = %(court_id)s'
                ' AND is_published = True',
            court_id=self.court_id,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_not_found(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = None

        with self.assertRaises(exc.NotFound):
            await court.read(court_id=self.court_id)

        mock_init.assert_called_with(
            sql='SELECT id, venue_id, number, is_published'
                '  FROM court'
                ' WHERE id = %(court_id)s'
                ' AND is_published = True',
            court_id=self.court_id,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_include_unpublished(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_court

        result = await court.read(court_id=self.court_id, include_unpublished=True)

        self.assertEqual(result, self.court)
        mock_init.assert_called_with(
            sql='SELECT id, venue_id, number, is_published'
                '  FROM court'
                ' WHERE id = %(court_id)s',
            court_id=self.court_id,
        )


class TestBrowse(AsyncTestCase):
    def setUp(self) -> None:
        self.venue_id = 1
        self.raw_court = [
            (1, 1, 1, True),
            (2, 1, 2, True),
        ]
        self.courts = [
            do.Court(
                id=1,
                venue_id=1,
                number=1,
                is_published=True,
            ),
            do.Court(
                id=2,
                venue_id=1,
                number=2,
                is_published=True,
            ),
        ]

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_court

        result = await court.browse(venue_id=self.venue_id)

        self.assertEqual(result, self.courts)
        mock_init.assert_called_with(
            sql='SELECT id, venue_id, number, is_published'
                '  FROM court'
                ' WHERE venue_id = %(venue_id)s'
                ' AND is_published = True',
            venue_id=self.venue_id,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    async def test_include_unpublished(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_court

        result = await court.browse(venue_id=self.venue_id, include_unpublished=True)

        self.assertEqual(result, self.courts)
        mock_init.assert_called_with(
            sql='SELECT id, venue_id, number, is_published'
                '  FROM court'
                ' WHERE venue_id = %(venue_id)s',
            venue_id=self.venue_id,
        )
