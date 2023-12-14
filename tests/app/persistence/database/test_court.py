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


class TestEdit(AsyncTestCase):
    def setUp(self) -> None:
        self.court_id = 1
        self.is_published = True

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock):
        result = await court.edit(
            court_id=self.court_id,
            is_published=self.is_published,
        )
        self.assertIsNone(result)
        mock_execute.assert_called_once()

    async def test_no_update(self):
        result = await court.edit(
            court_id=self.court_id,
            is_published=None,
        )
        self.assertIsNone(result)


class TestBatchAdd(AsyncTestCase):
    def setUp(self) -> None:
        self.venue_id = 1
        self.add = 3
        self.start_from = 3

        self.params = {
            'number_0': 3,
            'number_1': 4,
            'number_2': 5,
        }

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute, mock_init):
        mock_execute.return_value = None

        result = await court.batch_add(
            venue_id=self.venue_id,
            add=self.add,
            start_from=self.start_from,
        )

        self.assertIsNone(result)

        mock_init.assert_called_with(
            sql=fr'INSERT INTO court'
                fr'            (venue_id, number, is_published)'
                fr'     VALUES (%(venue_id)s, %(number_0)s, %(is_published)s),'
                fr' (%(venue_id)s, %(number_1)s, %(is_published)s),'
                fr' (%(venue_id)s, %(number_2)s, %(is_published)s)',
            venue_id=self.venue_id, is_published=True, **self.params,
        )
