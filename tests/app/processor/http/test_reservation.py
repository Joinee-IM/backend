from datetime import datetime

from freezegun import freeze_time

import app.exceptions as exc
from app.base import do, enums, vo
from app.processor.http import reservation
from app.utils import Response
from app.utils.security import AuthedAccount
from tests import AsyncMock, AsyncTestCase, MockContext, patch


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
        self.total_count = 1
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
            data=reservation.BrowseReservationOutput(
                data=self.reservations,
                total_count=self.total_count,
                limit=self.params.limit,
                offset=self.params.offset,
            ),
        )

    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock):
        mock_browse.return_value = self.reservations, self.total_count

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


class TestReadReservation(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.reservation = do.Reservation(
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
        )
        self.expect_result = Response(data=self.reservation)

    @patch('app.persistence.database.reservation.read', new_callable=AsyncMock)
    async def test_happy_path(self, mock_read: AsyncMock):
        mock_read.return_value = self.reservation

        result = await reservation.read_reservation(reservation_id=self.reservation_id)

        self.assertEqual(result, self.expect_result)
        mock_read.assert_called_with(
            reservation_id=self.reservation_id,
        )


class TestJoinReservation(AsyncTestCase):
    def setUp(self) -> None:
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4), role=enums.RoleType.normal)}
        self.invitation_code = 'code'
        self.account_id = 1
        self.reservation = do.Reservation(
            id=1,
            stadium_id=1,
            venue_id=1,
            court_id=1,
            start_time=datetime(2023, 11, 17, 11, 11, 11),
            end_time=datetime(2023, 11, 17, 13, 11, 11),
            member_count=1,
            vacancy=1,
            technical_level=[enums.TechnicalType.advanced],
            remark='remark',
            invitation_code='invitation_code',
            is_cancelled=False,
        )
        self.full_reservation = do.Reservation(
            id=1,
            stadium_id=1,
            venue_id=1,
            court_id=1,
            start_time=datetime(2023, 11, 17, 11, 11, 11),
            end_time=datetime(2023, 11, 17, 13, 11, 11),
            member_count=1,
            vacancy=-1,
            technical_level=[enums.TechnicalType.advanced],
            remark='remark',
            invitation_code='invitation_code',
            is_cancelled=False,
        )
        self.expect_result = Response(data=True)

    @patch('app.client.google_calendar.update_google_calendar_event', new_callable=AsyncMock)
    @patch('app.processor.http.reservation.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation.read_by_code', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation_member.batch_add', new_callable=AsyncMock)
    async def test_happy_path(
        self, mock_add: AsyncMock, mock_read: AsyncMock, mock_context: MockContext,
        mock_update_event: AsyncMock,
    ):
        mock_context._context = self.context
        mock_read.return_value = self.reservation

        result = await reservation.join_reservation(invitation_code=self.invitation_code)

        self.assertEqual(result, self.expect_result)
        mock_read.assert_called_with(invitation_code=self.invitation_code)
        mock_add.assert_called_with(
            reservation_id=self.reservation.id,
            member_ids=[self.account_id],
        )
        mock_update_event.assert_called_with(
            reservation_id=self.reservation.id,
            member_id=self.account_id,
        )

        mock_context.reset_context()

    @patch('app.processor.http.reservation.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation.read_by_code', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation_member.batch_add', new_callable=AsyncMock)
    async def test_reservation_full(self, mock_add: AsyncMock, mock_read: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_read.return_value = self.full_reservation

        with self.assertRaises(exc.ReservationFull):
            await reservation.join_reservation(invitation_code=self.invitation_code)

        mock_read.assert_called_with(invitation_code=self.invitation_code)
        mock_add.assert_not_called()
        mock_context.reset_context()


class TestDeleteReservation(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.account_id = 1
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=self.account_id, time=datetime(2023, 11, 4), role=enums.RoleType.provider)}
        self.reservation_members = [
            do.ReservationMember(
                reservation_id=self.reservation_id,
                account_id=self.account_id,
                is_joined=True,
                is_manager=True,
            ),
        ]
        self.expect_result = Response()

    @patch('app.processor.http.reservation.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation_member.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.delete', new_callable=AsyncMock)
    async def test_happy_path(self, mock_delete: AsyncMock, mock_browse: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_browse.return_value = self.reservation_members

        result = await reservation.delete_reservation(reservation_id=self.reservation_id)

        self.assertEqual(result, self.expect_result)
        mock_browse.assert_called_with(
            reservation_id=self.reservation_id,
            account_id=self.account_id,
        )
        mock_delete.assert_called_with(
            reservation_id=self.reservation_id,
        )
        mock_context.reset_context()

    @patch('app.processor.http.reservation.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation_member.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.delete', new_callable=AsyncMock)
    async def test_no_permission(self, mock_delete: AsyncMock, mock_browse: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_browse.return_value = []

        with self.assertRaises(exc.NoPermission):
            await reservation.delete_reservation(reservation_id=self.reservation_id)

        mock_browse.assert_called_with(
            reservation_id=self.reservation_id,
            account_id=self.account_id,
        )
        mock_delete.assert_not_called()
        mock_context.reset_context()


class TestEditReservation(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.account_id = 1
        self.context = {
            'AUTHED_ACCOUNT': AuthedAccount(id=self.account_id, time=datetime(2023, 11, 4), role=enums.RoleType.provider),
            'REQUEST_TIME': datetime(2023, 11, 11),
        }
        self.wrong_time_context = {
            'AUTHED_ACCOUNT': AuthedAccount(id=self.account_id, time=datetime(2023, 11, 4), role=enums.RoleType.provider),
            'REQUEST_TIME': datetime(2023, 11, 30),
        }
        self.data = reservation.EditReservationInput(
            court_id=1,
            start_time=datetime(2023, 11, 11, 11),
            end_time=datetime(2023, 11, 11, 13),
            vacancy=3,
            technical_levels=[enums.TechnicalType.advanced],
            remark='remark',
        )
        self.reservation_member = [
            do.ReservationMember(
                reservation_id=self.reservation_id,
                account_id=self.account_id,
                is_manager=True,
                is_joined=True,
            ),
        ]
        self.no_permission_reservation_member = [
            do.ReservationMember(
                reservation_id=self.reservation_id,
                account_id=self.account_id,
                is_manager=False,
                is_joined=True,
            ),
        ]
        self.reservation = do.Reservation(
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
        )
        self.court = do.Court(id=1, venue_id=1, is_published=True, number=1)
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
        self.different_reservations = [
            do.Reservation(
                id=2,
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
        self.expect_result = Response()

    @freeze_time('2023-11-11')
    @patch('app.processor.http.reservation.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation_member.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.read', new_callable=AsyncMock)
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.edit', new_callable=AsyncMock)
    async def test_happy_path(
        self, mock_edit: AsyncMock, mock_browse_reservation: AsyncMock,
        mock_read_venue: AsyncMock, mock_read_court: AsyncMock,
        mock_read_reservation: AsyncMock, mock_browse_member: AsyncMock,
        mock_context: MockContext,
    ):
        mock_context._context = self.context

        mock_browse_member.return_value = self.reservation_member
        mock_read_reservation.return_value = self.reservation
        mock_read_court.return_value = self.court
        mock_read_venue.return_value = self.venue
        mock_browse_reservation.return_value = self.reservations, None

        result = await reservation.edit_reservation(
            reservation_id=self.reservation_id,
            data=self.data,
        )

        self.assertEqual(result, self.expect_result)
        mock_edit.assert_called_with(
            reservation_id=self.reservation_id,
            court_id=self.court.id,
            venue_id=self.venue.id,
            stadium_id=self.venue.stadium_id,
            start_time=self.data.start_time,
            end_time=self.data.end_time,
            vacancy=self.data.vacancy,
            technical_levels=self.data.technical_levels,
            remark=self.data.remark,
        )

    @freeze_time('2023-11-11')
    @patch('app.processor.http.reservation.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation_member.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.read', new_callable=AsyncMock)
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.edit', new_callable=AsyncMock)
    async def test_court_reserve(
        self, mock_edit: AsyncMock, mock_browse_reservation: AsyncMock,
        mock_read_venue: AsyncMock, mock_read_court: AsyncMock,
        mock_read_reservation: AsyncMock, mock_browse_member: AsyncMock,
        mock_context: MockContext,
    ):
        mock_context._context = self.context

        mock_browse_member.return_value = self.reservation_member
        mock_read_reservation.return_value = self.reservation
        mock_read_court.return_value = self.court
        mock_read_venue.return_value = self.venue
        mock_browse_reservation.return_value = self.different_reservations, None

        with self.assertRaises(exc.CourtReserved):
            await reservation.edit_reservation(
                reservation_id=self.reservation_id,
                data=self.data,
            )
        mock_edit.assert_not_called()
        mock_context.reset_context()

    @freeze_time('2023-11-11')
    @patch('app.processor.http.reservation.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation_member.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.read', new_callable=AsyncMock)
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.edit', new_callable=AsyncMock)
    async def test_illegal_input_time(
        self, mock_edit: AsyncMock, mock_browse_reservation: AsyncMock,
        mock_read_venue: AsyncMock, mock_read_court: AsyncMock,
        mock_read_reservation: AsyncMock, mock_browse_member: AsyncMock,
        mock_context: MockContext,
    ):
        mock_context._context = self.wrong_time_context

        mock_browse_member.return_value = self.reservation_member
        mock_read_reservation.return_value = self.reservation
        mock_read_court.return_value = self.court
        mock_read_venue.return_value = self.venue
        mock_browse_reservation.return_value = self.different_reservations, None

        with self.assertRaises(exc.IllegalInput):
            await reservation.edit_reservation(
                reservation_id=self.reservation_id,
                data=self.data,
            )
        mock_browse_reservation.assert_not_called()
        mock_edit.assert_not_called()
        mock_context.reset_context()

    @freeze_time('2023-11-11')
    @patch('app.processor.http.reservation.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation_member.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.read', new_callable=AsyncMock)
    @patch('app.persistence.database.court.read', new_callable=AsyncMock)
    @patch('app.persistence.database.venue.read', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.edit', new_callable=AsyncMock)
    async def test_no_permission(
        self, mock_edit: AsyncMock, mock_browse_reservation: AsyncMock,
        mock_read_venue: AsyncMock, mock_read_court: AsyncMock,
        mock_read_reservation: AsyncMock, mock_browse_member: AsyncMock,
        mock_context: MockContext,
    ):
        mock_context._context = self.wrong_time_context

        mock_browse_member.return_value = self.no_permission_reservation_member
        mock_read_reservation.return_value = self.reservation
        mock_read_court.return_value = self.court
        mock_read_venue.return_value = self.venue
        mock_browse_reservation.return_value = self.different_reservations, None

        with self.assertRaises(exc.NoPermission):
            await reservation.edit_reservation(
                reservation_id=self.reservation_id,
                data=self.data,
            )
        mock_read_reservation.assert_not_called()
        mock_read_court.assert_not_called()
        mock_read_venue.assert_not_called()
        mock_browse_reservation.assert_not_called()
        mock_edit.assert_not_called()

        mock_context.reset_context()


class TestLeaveReservation(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.account_id = 1
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=self.account_id, time=datetime(2023, 11, 4), role=enums.RoleType.normal)}
        self.only_one_reservation_members = [
            do.ReservationMember(
                reservation_id=self.reservation_id,
                account_id=self.account_id,
                is_joined=True,
                is_manager=True,
            ),
        ]
        self.reservation_members = [
            do.ReservationMember(
                reservation_id=self.reservation_id,
                account_id=self.account_id,
                is_joined=True,
                is_manager=True,
            ),
            do.ReservationMember(
                reservation_id=self.reservation_id,
                account_id=2,
                is_joined=True,
                is_manager=True,
            ),
        ]
        self.expect_result = Response()

    @patch('app.processor.http.reservation.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation_member.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation_member.leave', new_callable=AsyncMock)
    async def test_happy_path(self, mock_leave: AsyncMock, mock_browse: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_browse.return_value = self.reservation_members

        result = await reservation.leave_reservation(
            reservation_id=self.reservation_id,
        )

        self.assertEqual(result, self.expect_result)
        mock_leave.assert_called_with(
            reservation_id=self.reservation_id,
            account_id=self.account_id,
        )

        mock_context.reset_context()

    @patch('app.processor.http.reservation.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation_member.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation.delete', new_callable=AsyncMock)
    async def test_delete_reservation(self, mock_delete: AsyncMock, mock_browse: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_browse.return_value = self.only_one_reservation_members

        result = await reservation.leave_reservation(
            reservation_id=self.reservation_id,
        )

        self.assertEqual(result, self.expect_result)
        mock_delete.assert_called_with(
            reservation_id=self.reservation_id,
        )

        mock_context.reset_context()

    @patch('app.processor.http.reservation.context', new_callable=MockContext)
    @patch('app.persistence.database.reservation_member.browse', new_callable=AsyncMock)
    @patch('app.persistence.database.reservation_member.leave', new_callable=AsyncMock)
    async def test_not_found(self, mock_leave: AsyncMock, mock_browse: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_browse.return_value = []

        with self.assertRaises(exc.NotFound):
            await reservation.leave_reservation(
                reservation_id=self.reservation_id,
            )
        mock_leave.assert_not_called()
        mock_context.reset_context()
