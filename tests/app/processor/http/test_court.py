from datetime import date, datetime, time
from uuid import UUID

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

        self.court = do.Court(id=self.court_id, venue_id=1, is_published=True, number=1)
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
            mock_read_court: AsyncMock,
    ):
        mock_read_court.return_value = self.court
        mock_browse_business_hour.return_value = self.business_hours
        mock_browse_reservation.return_value = self.reservations, 1

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
            mock_read_court: AsyncMock,
    ):
        mock_read_court.return_value = self.court
        mock_browse_business_hour.return_value = self.business_hours
        mock_browse_reservation.return_value = self.reservations, 1

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
            mock_read_court: AsyncMock,
    ):
        mock_read_court.return_value = self.court
        mock_browse_business_hour.return_value = self.business_hours
        mock_browse_reservation.return_value = self.reservations, 1

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
            mock_read_court: AsyncMock,
    ):
        mock_read_court.return_value = self.court
        mock_browse_business_hour.return_value = self.business_hours
        mock_browse_reservation.return_value = self.reservations, 1

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
            mock_read_court: AsyncMock,
    ):
        mock_read_court.return_value = self.court
        mock_browse_business_hour.side_effect = None
        mock_browse_reservation.return_value = self.reservations, 1
        with self.assertRaises(exc.NotFound):
            await court.browse_reservation_by_court_id(
                court_id=self.court_id,
                params=court.BrowseReservationParameters(),
            )


class TestAddReservation(AsyncTestCase):
    def setUp(self) -> None:
        self.court_id = 1
        self.account_id = 1
        self.data = court.AddReservationInput(
            start_time=datetime(2023, 11, 17, 11, 11, 11),
            end_time=datetime(2023, 11, 17, 13, 11, 11),
            technical_level=[enums.TechnicalType.advanced],
            remark='',
            member_count=1,
            vacancy=1,
            member_ids=[2],
        )
        self.unreservable_data = court.AddReservationInput(
            start_time=datetime(2023, 11, 30, 11, 11, 11),
            end_time=datetime(2023, 12, 1, 13, 11, 11),
            technical_level=[enums.TechnicalType.advanced],
            remark='',
            member_count=1,
            vacancy=1,
            member_ids=[2],
        )
        self.court = do.Court(
            id=1,
            venue_id=1,
            is_published=True,
            number=1,
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
        self.unreservable_venue = do.Venue(
            id=1,
            stadium_id=1,
            name='name',
            floor='floor',
            reservation_interval=1,
            is_reservable=False,
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
        self.account = do.Account(
            id=self.account_id, email='email@gmail.com', nickname='1',
            gender=enums.GenderType.female, image_uuid=UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c'),
            role=enums.RoleType.normal, is_verified=True, is_google_login=True,
        )
        self.member_accounts = [
            do.Account(
                id=self.account_id, email='email@gmail.com', nickname='1',
                gender=enums.GenderType.female, image_uuid=UUID('fad08f83-6ad7-429f-baa6-b1c3abf4991c'),
                role=enums.RoleType.normal, is_verified=True, is_google_login=True,
            ),
        ]
        self.reservation_id = 1
        self.invitation_code = 'code'
        self.context = {
            'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4), role=enums.RoleType.normal),
            'REQUEST_TIME': datetime(2023, 11, 17),
        }
        self.illegal_time_context = {
            'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4), role=enums.RoleType.normal),
            'REQUEST_TIME': datetime(2023, 11, 30),
        }
        self.wrong_account_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4), role=enums.RoleType.normal)}
        self.expect_result = Response(data=court.AddReservationOutput(id=self.reservation_id))
        self.location = f"{self.stadium.name} {self.venue.name} 第 {self.court.number} {self.venue.court_type}"
        self.members = [
            do.ReservationMember(
                account_id=2,
                reservation_id=self.reservation_id,
                is_manager=False,
                status=enums.ReservationMemberStatus.invited,
                source=enums.ReservationMemberSource.invitation_code,
            ),
            do.ReservationMember(
                account_id=1,
                reservation_id=self.reservation_id,
                is_manager=True,
                status=enums.ReservationMemberStatus.joined,
                source=enums.ReservationMemberSource.invitation_code,
            ),
        ]

    @freeze_time('2023-10-10')
    @patch('app.persistence.email.invitation.send', new_callable=AsyncMock)
    @patch('app.persistence.database.account.batch_read', new_callable=AsyncMock)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.database.account.read', new_callable=AsyncMock)
    @patch('app.client.google_calendar.add_google_calendar_event', new_callable=AsyncMock)
    @patch('app.processor.http.court.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    @patch('app.processor.http.court.invitation_code.generate', new_callable=Mock)
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.add', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation_member.batch_add_with_do', new_callable=AsyncMock)
    async def test_happy_path(
        self, mock_batch_add: AsyncMock, mock_add: AsyncMock, mock_read_venue: AsyncMock,
        mock_read_court: AsyncMock, mock_generate: Mock, mock_browse_reservation: AsyncMock,
        mock_context: MockContext, mock_add_event: AsyncMock, mock_read_account: AsyncMock,
        mock_read_stadium: AsyncMock, mock_batch_read: AsyncMock, mock_send_email: AsyncMock,
    ):
        mock_context._context = self.context
        mock_browse_reservation.return_value = None, 0
        mock_generate.return_value = self.invitation_code
        mock_read_court.return_value = self.court
        mock_read_venue.return_value = self.venue
        mock_add.return_value = self.reservation_id
        mock_read_account.return_value = self.account
        mock_read_stadium.return_value = self.stadium
        mock_batch_read.return_value = self.member_accounts

        result = await court.add_reservation(court_id=self.court_id, data=self.data)

        self.assertEqual(result, self.expect_result)
        mock_browse_reservation.assert_called_with(
            court_id=self.court_id,
            time_ranges=[
                vo.DateTimeRange(
                    start_time=self.data.start_time,
                    end_time=self.data.end_time,
                ),
            ],
        )
        mock_read_court.assert_called_with(court_id=self.court_id)
        mock_read_venue.assert_called_with(venue_id=self.court.venue_id)
        mock_read_stadium.assert_called_with(stadium_id=self.venue.stadium_id)
        mock_add.assert_called_with(
            court_id=self.court_id,
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
        mock_batch_add.assert_called_with(
            members=self.members,
        )
        mock_add_event.assert_called_with(
            reservation_id=self.reservation_id,
            start_time=self.data.start_time,
            end_time=self.data.end_time,
            account_id=self.account_id,
            location=self.location,
        )
        mock_send_email.assert_called_with(
            meet_code=self.invitation_code,
            bcc=', '.join(member.email for member in self.member_accounts),
        )

        mock_context.reset_context()

    @patch('app.processor.http.court.context', new_callable=MockContext)
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    async def test_illegal_time(
        self, mock_browse_reservation: AsyncMock, mock_read_venue: AsyncMock,
        mock_read_court: AsyncMock, mock_context: MockContext,
    ):
        mock_context._context = self.illegal_time_context
        mock_read_venue.return_value = self.venue
        mock_read_court.return_value = self.court
        mock_browse_reservation.return_value = None, 0

        with self.assertRaises(exc.IllegalInput):
            await court.add_reservation(court_id=self.court_id, data=self.data)

        mock_browse_reservation.assert_called_with(
            court_id=self.court_id,
            time_ranges=[
                vo.DateTimeRange(
                    start_time=self.data.start_time,
                    end_time=self.data.end_time,
                ),
            ],
        )

        mock_context.reset_context()

    @patch('app.processor.http.court.context', new_callable=MockContext)
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    async def test_court_reserve(
        self, mock_browse_reservation: AsyncMock, mock_read_venue: AsyncMock,
        mock_read_court: AsyncMock, mock_context: MockContext,
    ):
        mock_context._context = self.context
        mock_read_venue.return_value = self.venue
        mock_read_court.return_value = self.court
        mock_browse_reservation.return_value = self.reservations, 1

        with self.assertRaises(exc.CourtReserved):
            await court.add_reservation(court_id=self.court_id, data=self.data)

        mock_browse_reservation.assert_called_with(
            court_id=self.court_id,
            time_ranges=[
                vo.DateTimeRange(
                    start_time=self.data.start_time,
                    end_time=self.data.end_time,
                ),
            ],
        )

        mock_context.reset_context()

    @patch('app.processor.http.court.context', new_callable=MockContext)
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    async def test_venue_unreservable(
        self, mock_read_venue: AsyncMock, mock_read_court: AsyncMock,
        mock_context: MockContext,
    ):
        mock_context._context = self.context
        mock_read_court.return_value = self.court
        mock_read_venue.return_value = self.unreservable_venue

        with self.assertRaises(exc.VenueUnreservable):
            await court.add_reservation(
                court_id=self.court_id,
                data=self.data,
            )

        mock_context.reset_context()

    @patch('app.processor.http.court.context', new_callable=MockContext)
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    async def test_court_unreservable(
        self, mock_read_venue: AsyncMock, mock_read_court: AsyncMock,
        mock_context: MockContext,
    ):
        mock_context._context = self.context
        mock_read_court.return_value = self.court
        mock_read_venue.return_value = self.venue

        with self.assertRaises(exc.CourtUnreservable):
            await court.add_reservation(
                court_id=self.court_id,
                data=self.unreservable_data,
            )

        mock_context.reset_context()


class TestEditCourt(AsyncTestCase):
    def setUp(self) -> None:
        self.court_id =1
        self.data = court.EditCourtInput(
            is_published=True,
        )
        self.court = do.Court(id=self.court_id, venue_id=1, is_published=True, number=1)
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
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4), role=enums.RoleType.normal)}
        self.wrong_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4), role=enums.RoleType.normal)}
        self.expect_result = Response()

    @patch('app.processor.http.court.context', new_callable=MockContext)
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.database.court.edit', new_callable=AsyncMock)
    async def test_happy_path(
        self, mock_edit: AsyncMock, mock_read_stadium: AsyncMock, mock_read_venue: AsyncMock,
        mock_read_court: AsyncMock, mock_context: MockContext,
    ):
        mock_context._context = self.context
        mock_read_court.return_value = self.court
        mock_read_venue.return_value = self.venue
        mock_read_stadium.return_value = self.stadium

        result = await court.edit_court(
            court_id=self.court_id,
            data=self.data,
        )

        self.assertEqual(result, self.expect_result)
        mock_edit.assert_called_once()
        mock_context.reset_context()

    @patch('app.processor.http.court.context', new_callable=MockContext)
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.database.court.edit', new_callable=AsyncMock)
    async def test_no_permission(
        self, mock_edit: AsyncMock, mock_read_stadium: AsyncMock, mock_read_venue: AsyncMock,
        mock_read_court: AsyncMock, mock_context: MockContext,
    ):
        mock_context._context = self.wrong_context
        mock_read_court.return_value = self.court
        mock_read_venue.return_value = self.venue
        mock_read_stadium.return_value = self.stadium

        with self.assertRaises(exc.NoPermission):
            await court.edit_court(
                court_id=self.court_id,
                data=self.data,
            )

        mock_edit.assert_not_called()
        mock_context.reset_context()


class TestBatchAddCourt(AsyncTestCase):
    def setUp(self) -> None:
        self.venue_id = 1
        self.add = 3

        self.data = court.AddCourtInput(
            venue_id=self.venue_id,
            add=self.add,
        )

        self.expect_result = Response(data=True)
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4), role=enums.RoleType.provider)}
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
            court_count=2,
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

    @patch('app.persistence.database.court.batch_add', new_callable=AsyncMock)
    @patch('app.processor.http.court.context', new_callable=MockContext)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    async def test_happy_path(
        self, mock_read_venue: AsyncMock, mock_read_stadium: AsyncMock, mock_context: MockContext,
        mock_court_batch_add: AsyncMock,
    ):
        mock_context._context = self.context
        mock_read_venue.return_value = self.venue
        mock_read_stadium.return_value = self.stadium

        result = await court.batch_add_court(data=self.data)

        self.assertEqual(result, self.expect_result)

        mock_read_venue.assert_called_with(venue_id=self.venue_id)
        mock_read_stadium.assert_called_with(stadium_id=self.venue.stadium_id)
        mock_court_batch_add.assert_called_with(
            venue_id=self.venue_id,
            add=self.add,
            start_from=self.venue.court_count + 1,
        )
        mock_context.reset_context()

    @patch('app.persistence.database.court.batch_add', new_callable=AsyncMock)
    @patch('app.processor.http.court.context', new_callable=MockContext)
    @patch('app.persistence.database.stadium.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    async def test_no_permission(
        self, mock_read_venue: AsyncMock, mock_read_stadium: AsyncMock, mock_context: MockContext,
        mock_court_batch_add: AsyncMock,
    ):
        mock_context._context = self.wrong_context
        mock_read_venue.return_value = self.venue
        mock_read_stadium.return_value = self.stadium

        with self.assertRaises(exc.NoPermission):
            await court.batch_add_court(data=self.data)

        mock_court_batch_add.assert_not_called()
        mock_context.reset_context()
