from datetime import date, datetime, time

from freezegun import freeze_time

import app.exceptions as exc
from app.base import do, enums, vo
from app.processor.http import court
from app.utils import Response
from app.utils.security import AuthedAccount
from tests import AsyncMock, AsyncTestCase, Mock, MockContext, patch


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


class TestAddReservation(AsyncTestCase):
    def setUp(self) -> None:
        self.data = court.AddReservationInput(
            court_id=1,
            start_time=datetime(2023, 11, 11, 11, 11, 11),
            end_time=datetime(2023, 11, 11, 13, 11, 11),
            technical_level=[enums.TechnicalType.advanced],
            remark='',
            member_count=1,
            vacancy=1,
            member_id=[1],
        )
        self.court = do.Court(
            id=1,
            venue_id=1,
        )
        self.venue = do.Venue(
            id=1,
            stadium_id=1,
            name='name',
            floor='floor',
            reservation_interval=1,
            is_reservable=True,
            is_chargeable=True,
            area=1,
            capability=1,
            current_user_count=1,
            court_count=1,
            court_type='場',
            sport_id=1,
            fee_rate=1,
            fee_type=enums.FeeType.per_hour,
            sport_equipments='equipment',
            facilities='facility',
        )
        self.reservations = [do.Reservation(
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
        )]
        self.reservation_id = 1
        self.invitation_code = 'code'
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4))}
        self.wrong_account_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4))}
        self.expect_result = Response(data=court.AddReservationOutput(id=self.reservation_id))

    @freeze_time('2023-10-10')
    @patch('app.processor.http.court.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation.browse_by_court_id', new_callable=AsyncMock)
    @patch('app.processor.http.court.invitation_code.generate', new_callable=Mock)
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.add', new_callable=AsyncMock)
    async def test_happy_path(self, mock_add: AsyncMock, mock_read_venue: AsyncMock, mock_read_court: AsyncMock,
                              mock_generate: Mock, mock_browse_reservation: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_browse_reservation.return_value = None
        mock_generate.return_value = self.invitation_code
        mock_read_court.return_value = self.court
        mock_read_venue.return_value = self.venue
        mock_add.return_value = self.reservation_id

        result = await court.add_reservation(data=self.data)

        self.assertEqual(result, self.expect_result)
        mock_browse_reservation.assert_called_with(
            court_id=self.data.court_id,
            time_ranges=[vo.DateTimeRange(
                start_time=self.data.start_time,
                end_time=self.data.end_time,
            )]
        )
        mock_read_court.assert_called_with(court_id=self.data.court_id)
        mock_read_venue.assert_called_with(venue_id=self.court.venue_id)
        mock_add.assert_called_with(
            court_id=self.data.court_id,
            venue_id=self.venue.id,
            stadium_id=self.venue.stadium_id,
            start_time=self.data.start_time,
            end_time=self.data.end_time,
            technical_level=self.data.technical_level,
            invitation_code=self.invitation_code,
            remark=self.data.remark,
            member_count=self.data.member_count,
            vacancy=self.data.vacancy,
        )

        mock_context.reset_context()

    @freeze_time('2023-11-27')
    @patch('app.processor.http.court.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation.browse_by_court_id', new_callable=AsyncMock)
    async def test_illegal_time(self, mock_browse_reservation: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_browse_reservation.return_value = None

        with self.assertRaises(exc.IllegalInput):
            await court.add_reservation(data=self.data)

        mock_browse_reservation.assert_called_with(
            court_id=self.data.court_id,
            time_ranges=[vo.DateTimeRange(
                start_time=self.data.start_time,
                end_time=self.data.end_time,
            )]
        )

        mock_context.reset_context()

    @freeze_time('2023-11-27')
    @patch('app.processor.http.court.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation.browse_by_court_id', new_callable=AsyncMock)
    async def test_court(self, mock_browse_reservation: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_browse_reservation.return_value = self.reservations

        with self.assertRaises(exc.CourtReserved):
            await court.add_reservation(data=self.data)

        mock_browse_reservation.assert_called_with(
            court_id=self.data.court_id,
            time_ranges=[vo.DateTimeRange(
                start_time=self.data.start_time,
                end_time=self.data.end_time,
            )],
        )

        mock_context.reset_context()

    @freeze_time('2023-11-27')
    @patch('app.processor.http.court.context', new_callable=MockContext)
    async def test_court_reserved(self, mock_context: MockContext):
        mock_context._context = self.wrong_account_context

        with self.assertRaises(exc.NoPermission):
            await court.add_reservation(data=self.data)

        mock_context.reset_context()
