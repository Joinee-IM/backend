from datetime import date, datetime

import app.exceptions as exc
from app.base import do, enums, vo
from app.persistence.database import reservation
from tests import AsyncMock, AsyncTestCase, Mock, call, patch


class TestBrowse(AsyncTestCase):
    def setUp(self) -> None:
        self.court_id = 1
        self.time_ranges = [
            vo.DateTimeRange(
                start_time=datetime(2023, 11, 17, 11, 11, 11),
                end_time=datetime(2023, 11, 24, 13, 11, 11),
            ),
        ]
        self.start_date = date(2023, 11, 17)
        self.end_date = date(2023, 11, 24)
        self.is_cancelled = False

        self.params = {
            'court_id': self.court_id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'is_cancelled': self.is_cancelled,
            'start_time_0': self.time_ranges[0].start_time,
            'end_time_0': self.time_ranges[0].end_time,
        }

        self.raw_reservations = [
            (1, 1, 1, 1, datetime(2023, 11, 17), datetime(2023, 11, 17), 1, 1, ['ADVANCED'], '', '', False),
            (2, 2, 2, 2, datetime(2023, 11, 17), datetime(2023, 11, 17), 2, 2, ['ADVANCED'], '', '', False),
        ]
        self.total_count = 1

        self.reservations = [
            do.Reservation(
                id=id_,
                stadium_id=stadium_id,
                venue_id=venue_id,
                court_id=court_id,
                start_time=start_time,
                end_time=end_time,
                member_count=member_count,
                vacancy=vacancy,
                technical_level=technical_level,  # type: ignore
                remark=remark,
                invitation_code=invitation_code,
                is_cancelled=is_cancelled,
            )
            for id_, stadium_id, venue_id, court_id, start_time, end_time, member_count, vacancy, technical_level,
            remark, invitation_code, is_cancelled in self.raw_reservations
        ], self.total_count

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_fetch_all: AsyncMock, mock_init: Mock):
        mock_fetch_all.return_value = self.raw_reservations
        mock_fetch.return_value = self.total_count,

        result = await reservation.browse(
            court_id=self.court_id,
            time_ranges=self.time_ranges,
            start_date=self.start_date,
            end_date=self.end_date,
            is_cancelled=self.is_cancelled,
        )

        self.assertEqual(result, self.reservations)
        mock_init.assert_has_calls([
            call(
                sql='SELECT reservation.id, reservation.stadium_id, venue_id, court_id, start_time, end_time, member_count,'
                    '       vacancy, technical_level, remark, invitation_code, is_cancelled'
                    '  FROM reservation'
                    ' INNER JOIN stadium'
                    '         ON stadium.id = reservation.stadium_id'
                    ' INNER JOIN district'
                    '         ON stadium.district_id = district.id'
                    ' INNER JOIN venue'
                    '         ON venue.id = reservation.venue_id'
                    ' WHERE court_id = %(court_id)s AND start_time >= %(start_date)s AND end_time <= %(end_date)s'
                    ' AND is_cancelled = %(is_cancelled)s'
                    ' AND ((reservation.start_time < %(end_time_0)s AND reservation.end_time > %(start_time_0)s))'
                    ' ORDER BY start_time',
                **self.params, limit=None, offset=None,
            ),
            call(
                sql='SELECT COUNT(*)'
                    '  FROM ('
                    'SELECT reservation.id, reservation.stadium_id, venue_id, court_id, start_time, end_time, member_count,'
                    '       vacancy, technical_level, remark, invitation_code, is_cancelled'
                    '  FROM reservation'
                    ' INNER JOIN stadium'
                    '         ON stadium.id = reservation.stadium_id'
                    ' INNER JOIN district'
                    '         ON stadium.district_id = district.id'
                    ' INNER JOIN venue'
                    '         ON venue.id = reservation.venue_id'
                    ' WHERE court_id = %(court_id)s AND start_time >= %(start_date)s AND end_time <= %(end_date)s'
                    ' AND is_cancelled = %(is_cancelled)s'
                    ' AND ((reservation.start_time < %(end_time_0)s AND reservation.end_time > %(start_time_0)s))'
                    ' ORDER BY start_time) AS tbl',
                **self.params,
            ),
        ])

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_no_end_date(self, mock_fetch: AsyncMock, mock_fetch_all: AsyncMock, mock_init: Mock):
        mock_fetch_all.return_value = self.raw_reservations
        mock_fetch.return_value = self.total_count,

        result = await reservation.browse(
            court_id=self.court_id,
            time_ranges=self.time_ranges,
            start_date=self.start_date,
            is_cancelled=self.is_cancelled,
        )

        self.assertEqual(result, self.reservations)
        mock_init.assert_has_calls([
            call(
                sql='SELECT reservation.id, reservation.stadium_id, venue_id, court_id, start_time, end_time, member_count,'
                    '       vacancy, technical_level, remark, invitation_code, is_cancelled'
                    '  FROM reservation'
                    ' INNER JOIN stadium'
                    '         ON stadium.id = reservation.stadium_id'
                    ' INNER JOIN district'
                    '         ON stadium.district_id = district.id'
                    ' INNER JOIN venue'
                    '         ON venue.id = reservation.venue_id'
                    ' WHERE court_id = %(court_id)s AND start_time >= %(start_date)s AND end_time <= %(end_date)s'
                    ' AND is_cancelled = %(is_cancelled)s'
                    ' AND ((reservation.start_time < %(end_time_0)s AND reservation.end_time > %(start_time_0)s))'
                    ' ORDER BY start_time',
                **self.params, limit=None, offset=None,
            ),
            call(
                sql='SELECT COUNT(*)'
                    '  FROM ('
                    'SELECT reservation.id, reservation.stadium_id, venue_id, court_id, start_time, end_time, member_count,'
                    '       vacancy, technical_level, remark, invitation_code, is_cancelled'
                    '  FROM reservation'
                    ' INNER JOIN stadium'
                    '         ON stadium.id = reservation.stadium_id'
                    ' INNER JOIN district'
                    '         ON stadium.district_id = district.id'
                    ' INNER JOIN venue'
                    '         ON venue.id = reservation.venue_id'
                    ' WHERE court_id = %(court_id)s AND start_time >= %(start_date)s AND end_time <= %(end_date)s'
                    ' AND is_cancelled = %(is_cancelled)s'
                    ' AND ((reservation.start_time < %(end_time_0)s AND reservation.end_time > %(start_time_0)s))'
                    ' ORDER BY start_time) AS tbl',
                **self.params,
            ),
        ])


class TestAdd(AsyncTestCase):
    def setUp(self) -> None:
        self.stadium_id = 1
        self.venue_id = 1
        self.court_id = 1
        self.start_time = datetime(2023, 11, 11, 11, 11, 11)
        self.end_time = datetime(2023, 11, 11, 13, 11, 11)
        self.technical_level = [
            enums.TechnicalType.advanced,
        ]
        self.invitation_code = 'code'
        self.remark = 'remark'
        self.member_count = 1
        self.vacancy = -1

        self.expect_result = 1

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = 1,

        result = await reservation.add(
            stadium_id=self.stadium_id, venue_id=self.venue_id, court_id=self.court_id, start_time=self.start_time,
            end_time=self.end_time, technical_level=self.technical_level, invitation_code=self.invitation_code,
            remark=self.remark, member_count=self.member_count, vacancy=self.vacancy,
        )

        self.assertEqual(result, self.expect_result)
        mock_init.assert_called_with(
            sql=r'INSERT INTO reservation(stadium_id, venue_id, court_id, start_time, end_time, member_count, vacancy,'
                r'                        technical_level, remark, invitation_code)'
                r'                 VALUES(%(stadium_id)s, %(venue_id)s, %(court_id)s, %(start_time)s, %(end_time)s,'
                r'                        %(member_count)s, %(vacancy)s, %(technical_level)s, %(remark)s,'
                r'                        %(invitation_code)s)'
                r'  RETURNING id',
            stadium_id=self.stadium_id, venue_id=self.venue_id, court_id=self.court_id, start_time=self.start_time,
            end_time=self.end_time, member_count=self.member_count, vacancy=self.vacancy,
            technical_level=self.technical_level, remark=self.remark, invitation_code=self.invitation_code,
        )


class TestRead(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.raw_reservation = 1, 1, 1, 1, datetime(2023, 11, 17), datetime(2023, 11, 17), 1, 1, ['ADVANCED'], '', '', False, None  # noqa
        self.reservation = do.Reservation(
            id=1,
            stadium_id=1,
            venue_id=1,
            court_id=1,
            start_time=datetime(2023, 11, 17),
            end_time=datetime(2023, 11, 17),
            member_count=1,
            vacancy=1,
            technical_level=[enums.TechnicalType.advanced],
            remark='',
            invitation_code='',
            is_cancelled=False,
            google_event_id=None,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_reservation

        result = await reservation.read(reservation_id=self.reservation_id)

        self.assertEqual(result, self.reservation)
        mock_init.assert_called_with(
            sql=r'SELECT id, stadium_id, venue_id, court_id, start_time, end_time, member_count,'
                r'       vacancy, technical_level, remark, invitation_code, is_cancelled, google_event_id'
                r'  FROM reservation'
                r' WHERE id = %(reservation_id)s',
            reservation_id=self.reservation_id,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_not_found(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = None

        with self.assertRaises(exc.NotFound):
            await reservation.read(reservation_id=self.reservation_id)

        mock_init.assert_called_with(
            sql=r'SELECT id, stadium_id, venue_id, court_id, start_time, end_time, member_count,'
                r'       vacancy, technical_level, remark, invitation_code, is_cancelled, google_event_id'
                r'  FROM reservation'
                r' WHERE id = %(reservation_id)s',
            reservation_id=self.reservation_id,
        )


class TestReadByCode(AsyncTestCase):
    def setUp(self) -> None:
        self.invitation_code = 'code'
        self.raw_reservation = 1, 1, 1, 1, datetime(2023, 11, 17), datetime(2023, 11, 17), 1, 1, [
            'ADVANCED',
        ], '', '', False  # noqa
        self.reservation = do.Reservation(
            id=1,
            stadium_id=1,
            venue_id=1,
            court_id=1,
            start_time=datetime(2023, 11, 17),
            end_time=datetime(2023, 11, 17),
            member_count=1,
            vacancy=1,
            technical_level=[enums.TechnicalType.advanced],
            remark='',
            invitation_code='',
            is_cancelled=False,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_reservation

        result = await reservation.read_by_code(invitation_code=self.invitation_code)

        self.assertEqual(result, self.reservation)
        mock_init.assert_called_with(
            sql=r'SELECT id, stadium_id, venue_id, court_id, start_time, end_time, member_count,'
                r'       vacancy, technical_level, remark, invitation_code, is_cancelled'
                r'  FROM reservation'
                r' WHERE invitation_code = %(invitation_code)s',
            invitation_code=self.invitation_code,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_not_found(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = None

        with self.assertRaises(exc.NotFound):
            await reservation.read_by_code(invitation_code=self.invitation_code)

        mock_init.assert_called_with(
            sql=r'SELECT id, stadium_id, venue_id, court_id, start_time, end_time, member_count,'
                r'       vacancy, technical_level, remark, invitation_code, is_cancelled'
                r'  FROM reservation'
                r' WHERE invitation_code = %(invitation_code)s',
            invitation_code=self.invitation_code,
        )


class TestAddEventId(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.event_id = 'event_id'

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', AsyncMock(return_value=None))
    async def test_happy_path(self):
        result = await reservation.add_event_id(reservation_id=self.reservation_id, event_id=self.event_id)
        self.assertIsNone(result)


class TestGetManagerId(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.manager_id = 1

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.manager_id,

        result = await reservation.get_manager_id(reservation_id=self.reservation_id)

        self.assertEqual(result, self.manager_id)
        mock_init.assert_called_with(
            sql=r"SELECT reservation_member.account_id"
                r"  FROM reservation"
                r" INNER JOIN reservation_member ON reservation_member.reservation_id = reservation.id"
                r" WHERE reservation.id = %(reservation_id)s AND reservation_member.is_manager = TRUE",
            reservation_id=self.reservation_id,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_not_found(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = None

        with self.assertRaises(exc.NotFound):
            await reservation.get_manager_id(reservation_id=self.reservation_id)

        mock_init.assert_called_with(
            sql=r"SELECT reservation_member.account_id"
                r"  FROM reservation"
                r" INNER JOIN reservation_member ON reservation_member.reservation_id = reservation.id"
                r" WHERE reservation.id = %(reservation_id)s AND reservation_member.is_manager = TRUE",
            reservation_id=self.reservation_id,
        )


class TestEdit(AsyncTestCase):
    def setUp(self) -> None:
        self.reservation_id = 1
        self.stadium_id = 1
        self.venue_id = 1
        self.court_id = 1
        self.start_time = datetime(2023, 11, 11, 11)
        self.end_time = datetime(2023, 11, 11, 13)
        self.vacancy = 1
        self.technical_levels = [enums.TechnicalType.advanced]
        self.remark = ''

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = None

        result = await reservation.edit(
            reservation_id=self.reservation_id,
            stadium_id=self.stadium_id,
            venue_id=self.venue_id,
            court_id=self.court_id,
            start_time=self.start_time,
            end_time=self.start_time,
            vacancy=self.vacancy,
            technical_levels=self.technical_levels,
            remark=self.remark,
        )
        mock_init.assert_called_once()

        self.assertIsNone(result)

    async def test_no_update(self):
        result = await reservation.edit(reservation_id=self.reservation_id)
        self.assertIsNone(result)
