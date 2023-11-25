from datetime import datetime

from freezegun import freeze_time

from app.base import enums, vo
from app.persistence.database import view
from tests import AsyncMock, AsyncTestCase, Mock, patch


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
            (datetime(2023, 11, 11), datetime(2023, 11, 17), 'stadium_name', 'venue_name', True, 1, False),
        ]
        self.expect_result = [
            vo.ViewMyReservation(
                start_time=datetime(2023, 11, 11),
                end_time=datetime(2023, 11, 17),
                stadium_name='stadium_name',
                venue_name='venue_name',
                is_manager=True,
                vacancy=1,
                status=enums.ReservationStatus.finished,
            ),
        ]

    @freeze_time('2023-11-30')
    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    @patch('app.persistence.database.view.compose_reservation_status', new_callable=Mock)
    async def test_happy_path(self, mock_compose: Mock, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_reservation
        mock_compose.return_value = enums.ReservationStatus.finished

        result = await view.browse_my_reservation(
            account_id=self.account_id,
            sort_by=self.normal_sort,
            order=self.order,
            limit=self.limit,
            offset=self.offset,
        )

        self.assertEqual(result, self.expect_result)
        mock_init.assert_called_with(
            sql=r'SELECT start_time,'
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
            account_id=self.account_id, fetch='all', limit=self.limit, offset=self.offset,
        )


    @freeze_time('2023-11-30')
    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    @patch('app.persistence.database.view.compose_reservation_status', new_callable=Mock)
    async def test_sort_by_status(self, mock_compose: Mock, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_reservation
        mock_compose.return_value = enums.ReservationStatus.finished

        result = await view.browse_my_reservation(
            account_id=self.account_id,
            sort_by=self.sort_by_status,
            order=self.order,
            limit=self.limit,
            offset=self.offset,
        )

        self.assertEqual(result, self.expect_result)
        mock_init.assert_called_with(
            sql=r'SELECT start_time,'
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
            account_id=self.account_id, fetch='all', limit=self.limit, offset=self.offset,
        )


    @freeze_time('2023-11-30')
    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    @patch('app.persistence.database.view.compose_reservation_status', new_callable=Mock)
    async def test_sort_by_time(self, mock_compose: Mock, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_reservation
        mock_compose.return_value = enums.ReservationStatus.finished

        result = await view.browse_my_reservation(
            account_id=self.account_id,
            sort_by=self.sort_by_time,
            order=self.order,
            limit=self.limit,
            offset=self.offset,
        )

        self.assertEqual(result, self.expect_result)
        mock_init.assert_called_with(
            sql=r'SELECT start_time,'
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
            account_id=self.account_id, fetch='all', limit=self.limit, offset=self.offset,
        )
