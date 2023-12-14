from datetime import datetime, time
from unittest.mock import call, patch
from uuid import UUID

from fastapi import File, UploadFile
from starlette.datastructures import Headers

import app.exceptions as exc
from app.base import do, enums, vo
from app.const import BUCKET_NAME
from app.processor.http import album
from app.utils import AuthedAccount, Response
from tests import AsyncMock, AsyncTestCase, MockContext


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
            data=[
                album.BrowseAlbumOutput(
                    file_uuid=UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c'),
                    url=url,
                )
                for url in self.urls
            ],
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
            data=[
                album.BrowseAlbumOutput(
                    file_uuid=UUID('262b3702-1891-4e18-958e-82ebe758b0c9'),
                    url=url,
                )
                for url in self.urls
            ],
        )
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4), role=enums.RoleType.normal)}
        self.wrong_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4), role=enums.RoleType.normal)}

        self.venue = do.Venue(
            id=1,
            stadium_id=1,
            name='name',
            floor='floor',
            reservation_interval=1,
            is_reservable=True,
            is_chargeable=True,
            area=1,
            capacity=1,
            current_user_count=1,
            court_count=1,
            court_type='場',
            sport_id=1,
            fee_rate=1,
            fee_type=enums.FeeType.per_hour,
            sport_equipments='equipment',
            facilities='facility',
            is_published=True,
        )
        self.stadium = vo.ViewStadium(
            id=1,
            name='name',
            district_id=1,
            contact_number='0800092000',
            description='desc',
            owner_id=1,
            address='address1',
            long=3.14,
            lat=1.59,
            is_published=True,
            city='city1',
            district='district1',
            sports=['sport1'],
            business_hours=[
                do.BusinessHour(
                    id=1,
                    place_id=1,
                    type=enums.PlaceType.stadium,
                    weekday=1,
                    start_time=time(10, 27),
                    end_time=time(20, 27),
                ),
            ],
        )

    @patch('app.processor.http.album.context', new_callable=MockContext)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.file_storage.gcs.GCSHandler.sign_url', AsyncMock(return_value='url'))
    @patch('app.persistence.file_storage.gcs.GCSHandler.upload', new_callable=AsyncMock)
    @patch('app.persistence.database.album.batch_add', new_callable=AsyncMock)
    @patch('app.persistence.database.gcs_file.batch_add_with_do', new_callable=AsyncMock)
    async def test_happy_path(
        self, mock_add_gcs: AsyncMock, mock_add_album: AsyncMock, mock_upload: AsyncMock,
        mock_read_stadium: AsyncMock, mock_context: MockContext,
    ):
        mock_context._context = self.context
        mock_upload.return_value = self.file_uuid
        mock_read_stadium.return_value = self.stadium

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
        mock_context.reset_context()

    @patch('app.processor.http.album.context', new_callable=MockContext)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.file_storage.gcs.GCSHandler.sign_url', AsyncMock(return_value='url'))
    @patch('app.persistence.file_storage.gcs.GCSHandler.upload', new_callable=AsyncMock)
    @patch('app.persistence.database.album.batch_add', new_callable=AsyncMock)
    @patch('app.persistence.database.gcs_file.batch_add_with_do', new_callable=AsyncMock)
    async def test_wrong_content_type(
        self, mock_add_gcs: AsyncMock, mock_add_album: AsyncMock, mock_upload: AsyncMock,
        mock_read: AsyncMock, mock_context: MockContext,
    ):
        mock_context._context = self.context
        mock_read.return_value = self.stadium
        with self.assertRaises(exc.IllegalInput):
            await album.batch_add_album(place_type=self.place_type, place_id=self.place_id, files=self.reject_images)

        mock_upload.assert_not_called()
        mock_add_gcs.assert_not_called()
        mock_add_album.assert_not_called()
        mock_context.reset_context()

    @patch('app.processor.http.album.context', new_callable=MockContext)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.file_storage.gcs.GCSHandler.sign_url', AsyncMock(return_value='url'))
    @patch('app.persistence.file_storage.gcs.GCSHandler.upload', new_callable=AsyncMock)
    @patch('app.persistence.database.album.batch_add', new_callable=AsyncMock)
    @patch('app.persistence.database.gcs_file.batch_add_with_do', new_callable=AsyncMock)
    async def test_no_permission(
        self, mock_add_gcs: AsyncMock, mock_add_album: AsyncMock, mock_upload: AsyncMock,
        mock_read: AsyncMock, mock_context: MockContext,
    ):
        mock_context._context = self.wrong_context
        mock_read.return_value = self.stadium
        with self.assertRaises(exc.NoPermission):
            await album.batch_add_album(place_type=self.place_type, place_id=self.place_id, files=self.reject_images)

        mock_upload.assert_not_called()
        mock_add_gcs.assert_not_called()
        mock_add_album.assert_not_called()
        mock_context.reset_context()


class TestBatchDeleteAlbum(AsyncTestCase):
    def setUp(self) -> None:
        self.data = album.BatchDeleteAlbumInput(
            place_id=1,
            place_type=enums.PlaceType.venue,
            uuids=[UUID('262b3702-1891-4e18-958e-82ebe758b0c9'), UUID('262b3702-1891-4e18-958e-82ebe758b0c9')],
        )
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4), role=enums.RoleType.normal)}
        self.wrong_context = {
            'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4), role=enums.RoleType.normal),
        }

        self.venue = do.Venue(
            id=1,
            stadium_id=1,
            name='name',
            floor='floor',
            reservation_interval=1,
            is_reservable=True,
            is_chargeable=True,
            area=1,
            capacity=1,
            current_user_count=1,
            court_count=1,
            court_type='場',
            sport_id=1,
            fee_rate=1,
            fee_type=enums.FeeType.per_hour,
            sport_equipments='equipment',
            facilities='facility',
            is_published=True,
        )
        self.stadium = vo.ViewStadium(
            id=1,
            name='name',
            district_id=1,
            contact_number='0800092000',
            description='desc',
            owner_id=1,
            address='address1',
            long=3.14,
            lat=1.59,
            is_published=True,
            city='city1',
            district='district1',
            sports=['sport1'],
            business_hours=[
                do.BusinessHour(
                    id=1,
                    place_id=1,
                    type=enums.PlaceType.stadium,
                    weekday=1,
                    start_time=time(10, 27),
                    end_time=time(20, 27),
                ),
            ],
        )
        self.expect_result = Response()

    @patch('app.processor.http.album.context', new_callable=MockContext)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.database.album.batch_delete', AsyncMock())
    async def test_happy_path(self, mock_read_stadium: AsyncMock, mock_read_venue: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read_venue.return_value = self.venue
        mock_read_stadium.return_value = self.stadium

        result = await album.batch_delete_album(
            data=self.data,
        )

        self.assertEqual(result, self.expect_result)
        mock_context.reset_context()

    @patch('app.processor.http.album.context', new_callable=MockContext)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.database.album.batch_delete', AsyncMock())
    async def test_no_permission(self, mock_read_stadium: AsyncMock, mock_read_venue: AsyncMock, mock_context: MockContext):
        mock_context._context = self.wrong_context
        mock_read_venue.return_value = self.venue
        mock_read_stadium.return_value = self.stadium

        with self.assertRaises(exc.NoPermission):
            await album.batch_delete_album(
                data=self.data,
            )

        mock_context.reset_context()
