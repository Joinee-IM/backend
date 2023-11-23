from datetime import datetime

from app.base import do, enums, vo
from app.processor.http import reservation
from app.utils import Response
from tests import AsyncMock, AsyncTestCase, patch


class TestBrowseReservation(AsyncTestCase):
    def setUp(self) -> None:
        self.params = reservation.BrowseReservationParameters(
            city_id=1,
            district_id=1,
            sport_id=1,
            stadium_id=1,
            time_ranges=[
                vo.DateTimeRange(
                    start_time=datetime(2023, 11, 17, 11, 11, 11),
                    end_time=datetime(2023, 11, 24, 13, 11, 11),
                ),
            ],
            technical_level=enums.TechnicalType.advanced,
            limit=10,
            offset=0,
            sort_by=enums.BrowseReservationSortBy.time,
            order=enums.Sorter.desc,
        )

        self.reservations = [
            do.Reservation(
                id=1,
                stadium_id=1,
                venue_id=1,
                court_id=1,
                start_time=datetime(2023, 11, 17, 11, 11, 11),
                end_time=datetime(2023, 11, 17, 13, 11, 11),
                member_count=1,
                vacancy=0,
                technical_level=[enums.TechnicalType.advanced],
                remark='remark',
                invitation_code='invitation_code',
                is_cancelled=False,
            ),
        ]
        self.expect_result = Response(data=self.reservations)

    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock):
        mock_browse.return_value = self.reservations

        result = await reservation.browse_reservation(params=self.params)

        self.assertEqual(result, self.expect_result)
        mock_browse.assert_called_with(
            city_id=self.params.city_id,
            district_id=self.params.district_id,
            sport_id=self.params.sport_id,
            stadium_id=self.params.stadium_id,
            time_ranges=self.params.time_ranges,
            technical_level=self.params.technical_level,
            limit=self.params.limit,
            offset=self.params.offset,
            sort_by=self.params.sort_by,
            order=self.params.order,
        )
