from datetime import time
from unittest.mock import patch

from app.base import do, enums, vo
from app.processor.http import stadium
from app.utils import Response
from tests import AsyncMock, AsyncTestCase


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
                    )
                ]
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
                    )
                ]
            ),
        ]
        self.total_count = 1
        self.expect_result = Response(data=stadium.BrowseStadiumOutput(
            data=self.stadiums,
            total_count=self.total_count
        ))

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


class TestReadStadium(AsyncTestCase):
    def setUp(self) -> None:
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
                )
            ]
        )
        self.expect_result = Response(data=self.stadium)

    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    async def test_happy_path(self, mock_read: AsyncMock):
        mock_read.return_value = self.stadium

        result = await stadium.read_stadium(stadium_id=self.stadium_id)

        self.assertEqual(result, self.expect_result)
        mock_read.assert_called_with(
            stadium_id=self.stadium_id
        )
