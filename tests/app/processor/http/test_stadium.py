from datetime import datetime, time
from unittest.mock import patch

import app.exceptions as exc
from app.base import do, enums, vo
from app.processor.http import stadium
from app.utils import AuthedAccount, Response
from tests import AsyncMock, AsyncTestCase, Mock, MockContext


class TestBrowseStadium(AsyncTestCase):
    def setUp(self) -> None:
        self.params = stadium.StadiumSearchParameters(
            name='name',
            city_id=1,
            district_id=1,
            sport_id=1,
            time_ranges=[
                vo.WeekTimeRange(
                    weekday=1,
                    start_time=time(10, 27),
                    end_time=time(17, 27),
                ),
            ],
            limit=1,
            offset=1,
        )
        self.stadiums = [
            vo.ViewStadium(
                id=1,
                name='name',
                district_id=1,
                contact_number='0800092000',
                description='desc',
                owner_id=1,
                address='address',
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
            ),
            vo.ViewStadium(
                id=2,
                name='name2',
                district_id=2,
                contact_number='0800092001',
                description='desc2',
                owner_id=2,
                address='address',
                long=3.15,
                lat=1.58,
                is_published=True,
                city='city2',
                district='district2',
                sports=['sport2'],
                business_hours=[
                    do.BusinessHour(
                        id=2,
                        place_id=1,
                        type=enums.PlaceType.stadium,
                        weekday=1,
                        start_time=time(10, 27),
                        end_time=time(20, 27),
                    ),
                ],
            ),
        ]
        self.total_count = 1
        self.expect_result = Response(
            data=stadium.BrowseStadiumOutput(
                data=self.stadiums,
                total_count=self.total_count,
                limit=self.params.limit,
                offset=self.params.offset,
            ),
        )

    @patch('app.persistence.database.stadium.browse', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock):
        mock_browse.return_value = self.stadiums, self.total_count

        result = await stadium.browse_stadium(params=self.params)

        self.assertEqual(result, self.expect_result)
        mock_browse.assert_called_with(
            name=self.params.name,
            city_id=self.params.city_id,
            district_id=self.params.district_id,
            sport_id=self.params.sport_id,
            time_ranges=self.params.time_ranges,
            limit=self.params.limit,
            offset=self.params.offset,
        )


class TestBatchEditStadium(AsyncTestCase):
    def setUp(self):
        self.account_id = 1
        self.request_time = datetime(2023, 11, 11)
        self.context = {
            'AUTHED_ACCOUNT': AuthedAccount(id=self.account_id, time=datetime(2023, 11, 4), role=enums.RoleType.normal),
            'REQUEST_TIME': self.request_time,
        }
        self.data = stadium.BatchEditStadiumInput(
            stadium_ids=[1, 2],
            is_published=True,
        )
        self.stadiums = [
            do.Stadium(
                id=1,
                name='name',
                district_id=1,
                owner_id=1,
                address='address',
                contact_number='contact num',
                description='desc',
                long=3.14,
                lat=1.59,
                is_published=True,
            ),
        ]
        self.no_permission_stadiums = [
            do.Stadium(
                id=1,
                name='name',
                district_id=1,
                owner_id=2,
                address='address',
                contact_number='contact num',
                description='desc',
                long=3.14,
                lat=1.59,
                is_published=True,
            ),
        ]
        self.expect_result = Response()

    @patch('app.processor.http.stadium.context', new_callable=MockContext)
    @patch('app.persistence.database.stadium.batch_read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.batch_read', new_callable=AsyncMock)
    @patch('app.persistence.database.court.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.stadium.batch_edit', new_callable=AsyncMock)
    async def test_happy_path(
        self, mock_batch_edit: AsyncMock, mock_browse_court: AsyncMock,
        mock_batch_read_venue: AsyncMock, mock_batch_read: AsyncMock, mock_context: MockContext,
    ):
        mock_context._context = self.context

        mock_batch_read.return_value = self.stadiums
        mock_batch_read_venue.return_value = []
        mock_browse_court.return_value = []

        result = await stadium.batch_edit_stadium(data=self.data)

        self.assertEqual(result, self.expect_result)
        mock_batch_edit.assert_called()
        mock_context.reset_context()

    @patch('app.processor.http.stadium.context', new_callable=MockContext)
    @patch('app.persistence.database.stadium.batch_read', new_callable=AsyncMock)
    @patch('app.persistence.database.stadium.batch_edit', new_callable=AsyncMock)
    async def test_no_permission(self, mock_batch_edit: AsyncMock, mock_batch_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context

        mock_batch_read.return_value = self.no_permission_stadiums

        with self.assertRaises(exc.NoPermission):
            await stadium.batch_edit_stadium(data=self.data)

        mock_batch_edit.assert_not_called()
        mock_context.reset_context()


class TestReadStadium(AsyncTestCase):
    def setUp(self) -> None:
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4), role=enums.RoleType.provider)}
        self.stadium_id = 1
        self.stadium = vo.ViewStadium(
            id=1,
            name='name',
            district_id=1,
            contact_number='0800092000',
            description='desc',
            owner_id=1,
            address='address',
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
        self.expect_result = Response(data=self.stadium)

    @patch('app.processor.http.stadium.context', new_callable=MockContext)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    async def test_happy_path(self, mock_read: AsyncMock, mock_context: MockContext):
        mock_read.return_value = self.stadium
        mock_context._context = self.context

        result = await stadium.read_stadium(stadium_id=self.stadium_id)

        self.assertEqual(result, self.expect_result)
        mock_read.assert_called_with(
            stadium_id=self.stadium_id,
            include_unpublished=True,
        )
        mock_context.reset_context()


class TestEditStadium(AsyncTestCase):
    def setUp(self) -> None:
        self.stadium_id = 1
        self.data = stadium.EditStadiumInput(
            name='name',
            address='address',
            contact_number='contact_num',
            time_ranges=[
                vo.WeekTimeRange(
                    weekday=1,
                    start_time=time(8, 0, 0),
                    end_time=time(17, 0, 0),
                ),
            ],
            is_published=True,
        )
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4), role=enums.RoleType.provider)}
        self.wrong_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4), role=enums.RoleType.provider)}
        self.stadium = vo.ViewStadium(
            id=1,
            name='name',
            district_id=1,
            contact_number='0800092000',
            description='desc',
            owner_id=1,
            address='address',
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

    @patch('app.processor.http.stadium.context', new_callable=MockContext)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.database.stadium.edit', new_callable=AsyncMock)
    async def test_happy_path(self, mock_edit: AsyncMock, mock_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read.return_value = self.stadium

        result = await stadium.edit_stadium(
            stadium_id=self.stadium_id,
            data=self.data,
        )

        self.assertEqual(result, self.expect_result)
        mock_edit.assert_called_with(
            stadium_id=self.stadium_id,
            name=self.data.name,
            address=self.data.address,
            contact_number=self.data.contact_number,
            time_ranges=self.data.time_ranges,
            is_published=self.data.is_published,
        )

        mock_context.reset_context()

    @patch('app.processor.http.stadium.context', new_callable=MockContext)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.database.stadium.edit', new_callable=AsyncMock)
    async def test_no_permission(self, mock_edit: AsyncMock, mock_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.wrong_context
        mock_read.return_value = self.stadium

        with self.assertRaises(exc.NoPermission):
            await stadium.edit_stadium(
                stadium_id=self.stadium_id,
                data=self.data,
            )

        mock_edit.assert_not_called()
        mock_context.reset_context()


class TestAddStadium(AsyncTestCase):
    def setUp(self) -> None:
        self.data = stadium.AddStadiumInput(
            name='stadium',
            address='台北市大安區羅斯福路四段1號',
            district_id=1,
            business_hours=[
                vo.WeekTimeRange(
                    weekday=1,
                    start_time=time(8, 0),
                    end_time=time(12, 0),
                ),
                vo.WeekTimeRange(
                    weekday=1,
                    start_time=time(14, 0),
                    end_time=time(18, 0),
                ),
                vo.WeekTimeRange(
                    weekday=2,
                    start_time=time(8, 0),
                    end_time=time(18, 0),
                ),
            ],
            contact_number='0800000000',
            description='hi a new stadium',
        )
        self.stadium_id = 1

        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4), role=enums.RoleType.provider)}
        self.wrong_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4), role=enums.RoleType.normal)}

        self.expect_output = Response(data=stadium.AddStadiumOutput(id=self.stadium_id))

        self.long = 121.5397518
        self.lat = 25.0173405

    @patch('app.persistence.database.business_hour.batch_add', new_callable=AsyncMock)
    @patch('app.persistence.database.stadium.add', new_callable=AsyncMock)
    @patch('app.client.google_maps.google_maps.get_long_lat', new_callable=Mock)
    @patch('app.processor.http.stadium.context', new_callable=MockContext)
    async def test_happy_path(
            self, mock_context: AsyncMock,
            mock_gc_get_long_lat: Mock,
            mock_add_stadium: Mock,
            mock_add_hours: AsyncMock,
    ):
        mock_context._context = self.context
        mock_gc_get_long_lat.return_value = (self.long, self.lat)
        mock_add_stadium.return_value = self.stadium_id
        mock_add_hours.return_value = None

        result = await stadium.add_stadium(data=self.data)

        self.assertEqual(result, self.expect_output)

        mock_gc_get_long_lat.assert_called_with(address=self.data.address)
        mock_add_stadium.assert_called_with(
            name=self.data.name,
            address=self.data.address,
            district_id=self.data.district_id,
            owner_id=self.context['AUTHED_ACCOUNT'].id,
            contact_number=self.data.contact_number,
            description=self.data.description,
            long=self.long,
            lat=self.lat,
        )
        mock_add_hours.assert_called_with(
            place_type=enums.PlaceType.stadium,
            place_id=self.stadium_id,
            business_hours=self.data.business_hours,
        )

        mock_context.reset_context()

    @patch('app.processor.http.stadium.context', new_callable=MockContext)
    async def test_no_permission(
            self, mock_context: AsyncMock,
    ):
        mock_context._context = self.wrong_context

        with self.assertRaises(exc.NoPermission):
            await stadium.add_stadium(
                data=self.data,
            )

        mock_context.reset_context()


class TestValidateAddress(AsyncTestCase):
    def setUp(self) -> None:
        self.address = 'address'
        self.long = 125.333
        self.lat = 34.333
        self.expect_result = Response(data=stadium.ValidateAddressOutput(long=125.333, lat=34.333))

    @patch('app.client.google_maps.google_maps.get_long_lat', new_callable=Mock)
    async def test_happy_path(self, mock_get: Mock):
        mock_get.return_value = (self.long, self.lat)

        result = await stadium.validate_address(address=self.address)

        self.assertEqual(result, self.expect_result)
        mock_get.assert_called_with(
            address=self.address,
        )
