from datetime import date, datetime, time

from freezegun import freeze_time

import app.exceptions as exc
from app.base import do, enums, vo
from app.processor.http import court
from app.utils import Response
from tests import AsyncMock, AsyncTestCase, patch


class TestBrowseReservationByCourtId(AsyncTestCase):
    def setUp(self) -> None:
        self.court_id = 1
        self.time_ranges = [
            vo.DateTimeRange(
                start_time=datetime(2023, 11, 17, 11, 11, 11),
                end_time=datetime(2023, 11, 24, 13, 11, 11),
            ),
        ]
        self.no_available_time_range = [
            vo.DateTimeRange(
                start_time=datetime(2023, 11, 17, 11, 11, 11),
                end_time=datetime(2023, 11, 17, 13, 11, 11),
            ),
        ]
        self.start_date = date(2023, 11, 11)

        self.court = do.Court(id=self.court_id, venue_id=1)
        self.business_hours = [
            do.BusinessHour(
                id=1,
                place_id=1,
                type=enums.PlaceType.stadium,
                weekday=1,
                start_time=time(10, 27),
                end_time=time(17, 27),
            ),
        ]
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
        self.expect_result = Response(
            data=court.BrowseReservationOutput(
                start_date=self.time_ranges[0].start_time.date(),
                reservations=self.reservations,
            ),
        )
        self.query_with_start_date_expect_result = Response(
            data=court.BrowseReservationOutput(
                start_date=self.start_date,
                reservations=self.reservations,
            ),
        )
        self.no_param_expect_result = Response(
            data=court.BrowseReservationOutput(
                start_date=date(2023, 11, 11),
                reservations=self.reservations,
            ),
        )

    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.business_hour.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    async def test_happy_path(
            self,
            mock_browse_reservation: AsyncMock,
            mock_browse_business_hour: AsyncMock,
            mock_read_court: AsyncMock
    ):
        mock_read_court.return_value = self.court
        mock_browse_business_hour.return_value = self.business_hours
        mock_browse_reservation.return_value = self.reservations

        result = await court.browse_reservation_by_court_id(
            court_id=self.court_id,
            params=court.BrowseReservationParameters(
                time_ranges=self.time_ranges,
            ),
        )

        self.assertEqual(result, self.expect_result)

    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.business_hour.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    async def test_no_available_date(
            self,
            mock_browse_reservation: AsyncMock,
            mock_browse_business_hour: AsyncMock,
            mock_read_court: AsyncMock
    ):
        mock_read_court.return_value = self.court
        mock_browse_business_hour.return_value = self.business_hours
        mock_browse_reservation.return_value = self.reservations

        with self.assertRaises(exc.NotFound):
            await court.browse_reservation_by_court_id(
                court_id=self.court_id,
                params=court.BrowseReservationParameters(
                    time_ranges=self.no_available_time_range,
                ),
            )

    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.business_hour.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    async def test_query_with_start_date(
            self,
            mock_browse_reservation: AsyncMock,
            mock_browse_business_hour: AsyncMock,
            mock_read_court: AsyncMock
    ):
        mock_read_court.return_value = self.court
        mock_browse_business_hour.return_value = self.business_hours
        mock_browse_reservation.return_value = self.reservations

        result = await court.browse_reservation_by_court_id(
            court_id=self.court_id,
            params=court.BrowseReservationParameters(
                start_date=self.start_date,
            ),
        )

        self.assertEqual(result, self.query_with_start_date_expect_result)

    @freeze_time('2023-11-11 11:11:11')
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.business_hour.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    async def test_query_with_start_date(
            self,
            mock_browse_reservation: AsyncMock,
            mock_browse_business_hour: AsyncMock,
            mock_read_court: AsyncMock
    ):
        mock_read_court.return_value = self.court
        mock_browse_business_hour.return_value = self.business_hours
        mock_browse_reservation.return_value = self.reservations

        result = await court.browse_reservation_by_court_id(
            court_id=self.court_id,
            params=court.BrowseReservationParameters(),
        )

        self.assertEqual(result, self.no_param_expect_result)

    @freeze_time('2023-11-11 11:11:11')
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.business_hour.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    async def test_no_business_hour(
            self,
            mock_browse_reservation: AsyncMock,
            mock_browse_business_hour: AsyncMock,
            mock_read_court: AsyncMock
    ):
        mock_read_court.return_value = self.court
        mock_browse_business_hour.side_effect = None
        mock_browse_reservation.return_value = self.reservations
        with self.assertRaises(exc.NotFound):
            await court.browse_reservation_by_court_id(
                court_id=self.court_id,
                params=court.BrowseReservationParameters(),
            )
