from datetime import date, datetime

from app.base import do, enums, vo
from app.persistence.database import reservation
from tests import AsyncMock, AsyncTestCase, Mock, patch


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
                technical_level=[enums.TechnicalType(t) for t in technical_level],
                remark=remark,
                invitation_code=invitation_code,
                is_cancelled=is_cancelled,
            )
            for id_, stadium_id, venue_id, court_id, start_time, end_time, member_count, vacancy, technical_level,
            remark, invitation_code, is_cancelled in self.raw_reservations
        ]

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = self.raw_reservations

        result = await reservation.browse(
            court_id=self.court_id,
            time_ranges=self.time_ranges,
            start_date=self.start_date,
            end_date=self.end_date,
            is_cancelled=self.is_cancelled,
        )

        self.assertEqual(result, self.reservations)
        mock_init.assert_called_with(
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
                ' AND (reservation.start_time <= %(end_time_0)s AND reservation.end_time >= %(start_time_0)s)'
                ' ORDER BY start_time',
            fetch='all', **self.params, limit=None, offset=None
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_no_end_date(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = self.raw_reservations

        result = await reservation.browse(
            court_id=self.court_id,
            time_ranges=self.time_ranges,
            start_date=self.start_date,
            is_cancelled=self.is_cancelled,
        )

        self.assertEqual(result, self.reservations)
        mock_init.assert_called_with(
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
                ' AND (reservation.start_time <= %(end_time_0)s AND reservation.end_time >= %(start_time_0)s)'
                ' ORDER BY start_time',
            fetch='all', **self.params, limit=None, offset=None,
        )
