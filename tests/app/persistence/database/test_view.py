from datetime import datetime

from freezegun import freeze_time

from app.base import enums, vo
from app.persistence.database import view
from tests import AsyncMock, AsyncTestCase, Mock, call, patch


class TestBrowseMyReservation(AsyncTestCase):
    def setUp(self) -> None:
        self.account_id = 1
        self.normal_sort = enums.ViewMyReservationSortBy.stadium_name
        self.sort_by_time = enums.ViewMyReservationSortBy.time
        self.sort_by_status = enums.ViewMyReservationSortBy.status
        self.order = enums.Sorter.desc
        self.limit = 1
        self.offset = 0

        self.raw_reservation = [
            (1, datetime(2023, 11, 11), datetime(2023, 11, 17), 'stadium_name', 'venue_name', True, 1, False),
        ]
        self.total_count = 1
        self.expect_result = [
            vo.ViewMyReservation(
                reservation_id=1,
                start_time=datetime(2023, 11, 11),
                end_time=datetime(2023, 11, 17),
                stadium_name='stadium_name',
                venue_name='venue_name',
                is_manager=True,
                vacancy=1,
                status=enums.ReservationStatus.finished,
            ),
        ], self.total_count

    @freeze_time('2023-11-30')
    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    @patch('app.persistence.database.view.compose_reservation_status', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch_one: AsyncMock, mock_compose: Mock, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_reservation
        mock_compose.return_value = enums.ReservationStatus.finished
        mock_fetch_one.return_value = self.total_count,

        result = await view.browse_my_reservation(
            account_id=self.account_id,
            sort_by=self.normal_sort,
            order=self.order,
            limit=self.limit,
            offset=self.offset,
        )

        self.assertEqual(result, self.expect_result)
        mock_init.assert_has_calls([
            call(
                sql=r'SELECT reservation.id AS reservation_id,'
                    r'       start_time,'
                    r'       end_time,'
                    r'       stadium.name AS stadium_name,'
                    r'       venue.name AS venue_name,'
                    r'       is_manager,'
                    r'       vacancy,'
                    r'       is_cancelled'
                    r'  FROM reservation'
                    r' INNER JOIN venue ON venue.id = reservation.venue_id'
                    r' INNER JOIN stadium ON stadium.id = reservation.stadium_id'
                    r' INNER JOIN reservation_member'
                    r'         ON reservation_member.reservation_id = reservation.id'
                    r'        AND reservation_member.account_id = %(account_id)s'
                    fr' ORDER BY stadium_name DESC'
                    fr' LIMIT %(limit)s OFFSET %(offset)s',
                account_id=self.account_id, limit=self.limit, offset=self.offset,
            ),
            call(
                sql=r'SELECT COUNT(*)'
                    r'  FROM ('
                    r'SELECT reservation.id AS reservation_id,'
                    r'       start_time,'
                    r'       end_time,'
                    r'       stadium.name AS stadium_name,'
                    r'       venue.name AS venue_name,'
                    r'       is_manager,'
                    r'       vacancy,'
                    r'       is_cancelled'
                    r'  FROM reservation'
                    r' INNER JOIN venue ON venue.id = reservation.venue_id'
                    r' INNER JOIN stadium ON stadium.id = reservation.stadium_id'
                    r' INNER JOIN reservation_member'
                    r'         ON reservation_member.reservation_id = reservation.id'
                    r'        AND reservation_member.account_id = %(account_id)s'
                    fr' ORDER BY stadium_name DESC) AS tbl',
                account_id=self.account_id,
            ),
        ])

    @freeze_time('2023-11-30')
    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    @patch('app.persistence.database.view.compose_reservation_status', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_sort_by_status(self, mock_fetch_one: AsyncMock, mock_compose: Mock, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_reservation
        mock_compose.return_value = enums.ReservationStatus.finished
        mock_fetch_one.return_value = self.total_count,

        result = await view.browse_my_reservation(
            account_id=self.account_id,
            sort_by=self.sort_by_status,
            order=self.order,
            limit=self.limit,
            offset=self.offset,
        )

        self.assertEqual(result, self.expect_result)
        mock_init.assert_has_calls([
            call(
                sql=r'SELECT reservation.id AS reservation_id,'
                    r'       start_time,'
                    r'       end_time,'
                    r'       stadium.name AS stadium_name,'
                    r'       venue.name AS venue_name,'
                    r'       is_manager,'
                    r'       vacancy,'
                    r'       is_cancelled'
                    r'  FROM reservation'
                    r' INNER JOIN venue ON venue.id = reservation.venue_id'
                    r' INNER JOIN stadium ON stadium.id = reservation.stadium_id'
                    r' INNER JOIN reservation_member'
                    r'         ON reservation_member.reservation_id = reservation.id'
                    r'        AND reservation_member.account_id = %(account_id)s'
                    fr' ORDER BY (start_time, is_cancelled) DESC'
                    fr' LIMIT %(limit)s OFFSET %(offset)s',
                account_id=self.account_id, limit=self.limit, offset=self.offset,
            ),
            call(
                sql=r'SELECT COUNT(*)'
                    r'  FROM ('
                    r'SELECT reservation.id AS reservation_id,'
                    r'       start_time,'
                    r'       end_time,'
                    r'       stadium.name AS stadium_name,'
                    r'       venue.name AS venue_name,'
                    r'       is_manager,'
                    r'       vacancy,'
                    r'       is_cancelled'
                    r'  FROM reservation'
                    r' INNER JOIN venue ON venue.id = reservation.venue_id'
                    r' INNER JOIN stadium ON stadium.id = reservation.stadium_id'
                    r' INNER JOIN reservation_member'
                    r'         ON reservation_member.reservation_id = reservation.id'
                    r'        AND reservation_member.account_id = %(account_id)s'
                    fr' ORDER BY (start_time, is_cancelled) DESC) AS tbl',
                account_id=self.account_id,
            ),
        ])

    @freeze_time('2023-11-30')
    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    @patch('app.persistence.database.view.compose_reservation_status', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_sort_by_time(self, mock_fetch_one: AsyncMock, mock_compose: Mock, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_reservation
        mock_compose.return_value = enums.ReservationStatus.finished
        mock_fetch_one.return_value = self.total_count,

        result = await view.browse_my_reservation(
            account_id=self.account_id,
            sort_by=self.sort_by_time,
            order=self.order,
            limit=self.limit,
            offset=self.offset,
        )

        self.assertEqual(result, self.expect_result)
        mock_init.assert_has_calls([
            call(
                sql=r'SELECT reservation.id AS reservation_id,'
                    r'       start_time,'
                    r'       end_time,'
                    r'       stadium.name AS stadium_name,'
                    r'       venue.name AS venue_name,'
                    r'       is_manager,'
                    r'       vacancy,'
                    r'       is_cancelled'
                    r'  FROM reservation'
                    r' INNER JOIN venue ON venue.id = reservation.venue_id'
                    r' INNER JOIN stadium ON stadium.id = reservation.stadium_id'
                    r' INNER JOIN reservation_member'
                    r'         ON reservation_member.reservation_id = reservation.id'
                    r'        AND reservation_member.account_id = %(account_id)s'
                    fr' ORDER BY start_time DESC'
                    fr' LIMIT %(limit)s OFFSET %(offset)s',
                account_id=self.account_id, limit=self.limit, offset=self.offset,
            ),
            call(
                sql=r'SELECT COUNT(*)'
                    r'  FROM ('
                    r'SELECT reservation.id AS reservation_id,'
                    r'       start_time,'
                    r'       end_time,'
                    r'       stadium.name AS stadium_name,'
                    r'       venue.name AS venue_name,'
                    r'       is_manager,'
                    r'       vacancy,'
                    r'       is_cancelled'
                    r'  FROM reservation'
                    r' INNER JOIN venue ON venue.id = reservation.venue_id'
                    r' INNER JOIN stadium ON stadium.id = reservation.stadium_id'
                    r' INNER JOIN reservation_member'
                    r'         ON reservation_member.reservation_id = reservation.id'
                    r'        AND reservation_member.account_id = %(account_id)s'
                    fr' ORDER BY start_time DESC) AS tbl',
                account_id=self.account_id,
            ),
        ])
