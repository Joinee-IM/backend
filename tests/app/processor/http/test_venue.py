from unittest.mock import patch

from app.base import do, enums
from app.processor.http import venue
from tests import AsyncMock, AsyncTestCase


class TestBrowseVenue(AsyncTestCase):
    def setUp(self) -> None:
        self.params = venue.VenueSearchParameters(
            name='name',
            sport_id=1,
            is_reservable=True,
            sort_by=enums.VenueAvailableSortBy.current_user_count,
            order=enums.Sorter.desc,
            limit=10,
            offset=0,
        )
        self.venues = [
            do.Venue(
                id=1,
                stadium_id=1,
                name='name',
                floor='floor',
                reservation_interval=1,
                is_reservable=True,
                area=1,
                capability=1,
                current_user_count=1,
                court_count=1,
                court_type='場',
                is_chargeable=True,
                sport_id=1,
                fee_rate=1,
                fee_type=enums.FeeType.per_hour,
                sport_equipments='equipment',
                facilities='facility',
            ),
            do.Venue(
                id=2,
                stadium_id=2,
                name='name2',
                floor='floor2',
                reservation_interval=2,
                is_reservable=False,
                area=2,
                capability=2,
                current_user_count=2,
                court_count=2,
                court_type='場',
                is_chargeable=False,
                sport_id=2,
                fee_rate=2,
                fee_type=enums.FeeType.per_person,
                sport_equipments='equipment1',
                facilities='facility1',
            ),
        ]
        self.expect_result = venue.Response(data=self.venues)

    @patch('app.persistence.database.venue.browse', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock):
        mock_browse.return_value = self.venues

        result = await venue.browse_venue(params=self.params)

        self.assertEqual(result, self.expect_result)
        mock_browse.assert_called_with(
            name=self.params.name,
            sport_id=self.params.sport_id,
            is_reservable=self.params.is_reservable,
            sort_by=self.params.sort_by,
            order=self.params.order,
            limit=self.params.limit,
            offset=self.params.offset,
        )
