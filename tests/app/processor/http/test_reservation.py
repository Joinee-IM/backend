from datetime import datetime

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
        self.expect_result = Response(data=reservation.BrowseReservationOutput(
            data=self.reservations,
            total_count=self.total_count,
        ))

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
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4))}
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
    async def test_happy_path(self, mock_add: AsyncMock, mock_read: AsyncMock, mock_context: MockContext, mock_update_event: AsyncMock):
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
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=self.account_id, time=datetime(2023, 11, 4))}
        self.reservation_members = [
            do.ReservationMember(
                reservation_id=self.reservation_id,
                account_id=self.account_id,
                is_joined=True,
                is_manager=True,
            )
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
