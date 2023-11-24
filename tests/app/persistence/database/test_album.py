from unittest.mock import patch
from uuid import UUID

from app.base import do, enums
from app.persistence.database import album
from tests import AsyncMock, AsyncTestCase, Mock


class TestBrowse(AsyncTestCase):
    def setUp(self) -> None:
        self.place_type = enums.PlaceType.stadium
        self.place_id = 1
        self.raw_albums = [
            (1, 1, 'STADIUM', 'fad08f83-6ad7-429f-baa6-b1c3abf4991c'),
            (2, 2, 'VENUE', 'fad08f83-6ad7-429f-baa6-b1c3abf4991c'),
        ]
        self.albums = [
            do.Album(
                id=1,
                place_id=1,
                type=enums.PlaceType.stadium,
                file_uuid=UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c'),
            ),
            do.Album(
                id=2,
                place_id=2,
                type=enums.PlaceType.venue,
                file_uuid=UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c'),
            ),
        ]

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = self.raw_albums

        result = await album.browse(
            place_type=self.place_type,
            place_id=self.place_id,
        )

        self.assertEqual(result, self.albums)

        mock_init.assert_called_with(
            sql=r'SELECT id, place_id, type, file_uuid'
                r'  FROM album'
                r' WHERE place_id = %(place_id)s AND type = %(place_type)s',
            place_id=self.place_id, place_type=self.place_type, fetch='all',
        )
