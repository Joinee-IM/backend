from datetime import datetime, time
from unittest.mock import patch

import app.exceptions as exc
from app.base import do, enums, vo
from app.processor.http import venue
from app.utils import AuthedAccount, Response
from tests import AsyncMock, AsyncTestCase, MockContext


class TestBrowseVenue(AsyncTestCase):
    def setUp(self) -> None:
        self.params = venue.VenueSearchParameters(
            name='name',
            sport_id=1,
            stadium_id=1,
            is_reservable=True,
            sort_by=enums.VenueAvailableSortBy.current_user_count,
            order=enums.Sorter.desc,
            limit=10,
            offset=0,
        )
        self.total_count = 1
        self.venues = [
            do.Venue(
                id=1,
                stadium_id=1,
                name='name',
                floor='floor',
                reservation_interval=1,
                is_reservable=True,
                area=1,
                capacity=1,
                current_user_count=1,
                court_count=1,
                court_type='場',
                is_chargeable=True,
                sport_id=1,
                fee_rate=1,
                fee_type=enums.FeeType.per_hour,
                sport_equipments='equipment',
                facilities='facility',
                is_published=True,
            ),
            do.Venue(
                id=2,
                stadium_id=2,
                name='name2',
                floor='floor2',
                reservation_interval=2,
                is_reservable=False,
                area=2,
                capacity=2,
                current_user_count=2,
                court_count=2,
                court_type='場',
                is_chargeable=False,
                sport_id=2,
                fee_rate=2,
                fee_type=enums.FeeType.per_person,
                sport_equipments='equipment1',
                facilities='facility1',
                is_published=True,
            ),
        ]
        self.expect_result = venue.Response(
            data=venue.BrowseVenueOutput(
                data=self.venues, total_count=self.total_count,
                limit=self.params.limit, offset=self.params.offset
            ),
        )

    @patch('app.persistence.database.venue.browse', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock):
        mock_browse.return_value = self.venues, self.total_count

        result = await venue.browse_venue(params=self.params)

        self.assertEqual(result, self.expect_result)
        mock_browse.assert_called_with(
            name=self.params.name,
            sport_id=self.params.sport_id,
            stadium_id=self.params.stadium_id,
            is_reservable=self.params.is_reservable,
            sort_by=self.params.sort_by,
            order=self.params.order,
            limit=self.params.limit,
            offset=self.params.offset,
        )


class TestReadVenue(AsyncTestCase):
    def setUp(self) -> None:
        self.venue_id = 1
        self.venue = do.Venue(
            id=1,
            stadium_id=1,
            name='name',
            floor='floor',
            reservation_interval=1,
            is_reservable=True,
            area=1,
            capacity=1,
            current_user_count=1,
            court_count=1,
            court_type='場',
            is_chargeable=True,
            sport_id=1,
            fee_rate=1,
            fee_type=enums.FeeType.per_hour,
            sport_equipments='equipment',
            facilities='facility',
            is_published=True,
        )
        self.expect_result = Response(data=self.venue)

    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    async def test_happy_path(self, mock_read: AsyncMock):
        mock_read.return_value = self.venue

        result = await venue.read_venue(venue_id=self.venue_id)

        self.assertEqual(result, self.expect_result)
        mock_read.assert_called_with(
            venue_id=self.venue_id
        )


class TestBrowseCourt(AsyncTestCase):
    def setUp(self) -> None:
        self.venue_id = 1
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
        self.expect_result = Response(
            data=self.courts,
        )

    @patch('app.persistence.database.court.browse', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock):
        mock_browse.return_value = self.courts

        result = await venue.browse_court_by_venue_id(venue_id=self.venue_id)

        self.assertEqual(result, self.expect_result)
        mock_browse.assert_called_with(
            venue_id=self.venue_id,
        )


class TestEditVenue(AsyncTestCase):
    def setUp(self) -> None:
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4))}
        self.wrong_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4))}

        self.data = venue.EditVenueInput(
            name='name',
            floor='floor',
            area=1,
            capacity=1,
            sport_id=1,
            is_reservable=True,
            reservation_interval=1,
            is_chargeable=True,
            fee_rate=1,
            fee_type=enums.FeeType.per_hour,
            sport_equipments='s',
            facilities='f',
            court_type='1',
        )
        self.venue = do.Venue(
            id=1,
            stadium_id=1,
            name='name',
            floor='floor',
            reservation_interval=1,
            is_reservable=True,
            area=1,
            capacity=1,
            current_user_count=1,
            court_count=1,
            court_type='場',
            is_chargeable=True,
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
                )
            ],
        )
        self.expect_result = Response()

    @patch('app.processor.http.venue.context', new_callable=MockContext)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.edit', new_callable=AsyncMock)
    async def test_happy_path(self, mock_edit: AsyncMock, mock_read_stadium: AsyncMock,
                              mock_read_venue: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read_venue.return_value = self.venue
        mock_read_stadium.return_value = self.stadium

        result = await venue.edit_venue(
            venue_id=self.venue.id,
            data=self.data,
        )
        self.assertEqual(result, self.expect_result)

        mock_edit.assert_called_with(
            venue_id=self.venue.id,
            **self.data.model_dump(),
        )
        mock_context.reset_context()

    @patch('app.processor.http.venue.context', new_callable=MockContext)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.edit', new_callable=AsyncMock)
    async def test_no_permission(self, mock_edit: AsyncMock, mock_read_stadium: AsyncMock,
                                 mock_read_venue: AsyncMock, mock_context: MockContext):
        mock_context._context = self.wrong_context
        mock_read_venue.return_value = self.venue
        mock_read_stadium.return_value = self.stadium

        with self.assertRaises(exc.NoPermission):
            await venue.edit_venue(
                venue_id=self.venue.id,
                data=self.data,
            )

        mock_edit.assert_not_called()
        mock_context.reset_context()
