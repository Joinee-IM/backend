from unittest.mock import patch
from uuid import UUID

from app.base import do, enums
from app.processor.http import album
from app.utils import Response
from tests import AsyncMock, AsyncTestCase


class TestBrowseAlbum(AsyncTestCase):
    def setUp(self) -> None:
        self.params = album.BrowseAlbumInput(
            place_id=1,
            place_type=enums.PlaceType.stadium,
        )
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
        self.urls = ['url', 'url']
        self.expect_result = Response(
            data=album.BrowseAlbumOutput(urls=self.urls)
        )

    @patch('app.persistence.database.album.browse', new_callable=AsyncMock)
    @patch('app.persistence.file_storage.gcs.GCSHandler.sign_url', AsyncMock(return_value='url'))
    async def test_happy_path(self, mock_browse: AsyncMock):
        mock_browse.return_value = self.albums

        result = await album.browse_album(params=self.params)

        self.assertEqual(result, self.expect_result)
        mock_browse.assert_called_with(
            place_type=self.params.place_type,
            place_id=self.params.place_id,
        )
