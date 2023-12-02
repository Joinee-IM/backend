from unittest.mock import call, patch
from uuid import UUID

from fastapi import File, UploadFile
from starlette.datastructures import Headers

import app.exceptions as exc
from app.base import do, enums
from app.const import BUCKET_NAME
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
            data=album.BrowseAlbumOutput(urls=self.urls),
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


class TestAddAlbum(AsyncTestCase):
    def setUp(self) -> None:
        self.place_id = 1
        self.place_type = enums.PlaceType.stadium

        self.accept_header = Headers({
            'content-disposition': 'form-data; name="image"; filename="262b3702-1891-4e18-958e-82ebe758b0c9.jpeg"',
            'content-type': 'image/jpeg',
        })
        self.reject_header = Headers({
            'content-disposition': 'form-data; name="image"; filename="262b3702-1891-4e18-958e-82ebe758b0c9.HEIC"',
            'content-type': 'image/heic',
        })

        self.images = [
            UploadFile(File('asdf'), headers=self.accept_header),
            UploadFile(File('asdf'), headers=self.accept_header),
        ]
        self.reject_images = [
            UploadFile(File('fail'), headers=self.reject_header),
        ]

        self.file_uuid = UUID('262b3702-1891-4e18-958e-82ebe758b0c9')
        self.file_uuids = [UUID('262b3702-1891-4e18-958e-82ebe758b0c9'), UUID('262b3702-1891-4e18-958e-82ebe758b0c9')]

        self.bucket_name = BUCKET_NAME

        self.gcs_files = [
            do.GCSFile(
                uuid=uuid,
                key=str(uuid),
                bucket=BUCKET_NAME,
                filename=str(uuid),
            ) for uuid in self.file_uuids
        ]

        self.urls = ['url', 'url']
        self.expect_result = Response(
            data=album.BrowseAlbumOutput(urls=self.urls),
        )

    @patch('app.persistence.file_storage.gcs.GCSHandler.sign_url', AsyncMock(return_value='url'))
    @patch('app.persistence.file_storage.gcs.GCSHandler.upload', new_callable=AsyncMock)
    @patch('app.persistence.database.album.batch_add', new_callable=AsyncMock)
    @patch('app.persistence.database.gcs_file.batch_add_with_do', new_callable=AsyncMock)
    async def test_happy_path(self, mock_add_gcs: AsyncMock, mock_add_album: AsyncMock, mock_upload: AsyncMock):
        mock_upload.return_value = self.file_uuid

        result = await album.batch_add_album(place_type=self.place_type, place_id=self.place_id, files=self.images)

        self.assertEqual(result, self.expect_result)

        expected_calls = [
            call(file=self.images[0].file, content_type=self.images[0].content_type, bucket_name=self.bucket_name),
            call(file=self.images[1].file, content_type=self.images[1].content_type, bucket_name=self.bucket_name),
        ]
        mock_upload.assert_has_calls(expected_calls, any_order=False)

        mock_add_gcs.assert_called_with(
            self.gcs_files,
        )
        mock_add_album.assert_called_with(
            place_type=self.place_type,
            place_id=self.place_id,
            uuids=self.file_uuids,
        )

    @patch('app.persistence.file_storage.gcs.GCSHandler.sign_url', AsyncMock(return_value='url'))
    @patch('app.persistence.file_storage.gcs.GCSHandler.upload', new_callable=AsyncMock)
    @patch('app.persistence.database.album.batch_add', new_callable=AsyncMock)
    @patch('app.persistence.database.gcs_file.batch_add_with_do', new_callable=AsyncMock)
    async def test_wrong_content_type(self, mock_add_gcs: AsyncMock, mock_add_album: AsyncMock, mock_upload: AsyncMock):
        with self.assertRaises(exc.IllegalInput):
            await album.batch_add_album(place_type=self.place_type, place_id=self.place_id, files=self.reject_images)

        mock_upload.assert_not_called()
        mock_add_gcs.assert_not_called()
        mock_add_album.assert_not_called()
