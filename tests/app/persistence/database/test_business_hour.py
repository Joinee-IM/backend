from datetime import time
from unittest.mock import patch

from app.base import do, enums, vo
from app.persistence.database import business_hour
from tests import AsyncMock, AsyncTestCase, Mock


class TestBrowse(AsyncTestCase):
    def setUp(self) -> None:
        self.place_type = enums.PlaceType.stadium
        self.place_id = 1
        self.time_ranges = [
            vo.WeekTimeRange(
                weekday=1,
                start_time=time(10, 27),
                end_time=time(17, 27),
            ),
        ]

        self.params = {
            'place_id': self.place_id,
            'place_type': self.place_type,
            'weekday_0': 1,
            'start_time_0': time(10, 27),
            'end_time_0': time(17, 27),
        }
        self.params_no_time_range = {
            'place_id': self.place_id,
            'place_type': self.place_type,
        }
        self.raw_business_hour = [
            (1, self.place_id, self.place_type, 1, time(10, 27), time(17, 27)),
            (1, self.place_id, self.place_type, 2, time(10, 27), time(17, 27)),
        ]
        self.business_hour = [
            do.BusinessHour(
                id=id_,
                place_id=place_id,
                type=type_,
                weekday=weekday,
                start_time=start_time,
                end_time=end_time,
            )
            for id_, place_id, type_, weekday, start_time, end_time in self.raw_business_hour
        ]

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = self.raw_business_hour

        result = await business_hour.browse(
            place_id=self.place_id,
            place_type=self.place_type,
            time_ranges=self.time_ranges,
        )

        self.assertEqual(result, self.business_hour)
        mock_init.assert_called_with(
            sql='SELECT id, place_id, type, weekday, start_time, end_time'
                '  FROM business_hour'
                ' WHERE type = %(place_type)s'
                ' AND place_id = %(place_id)s'
                ' AND (business_hour.weekday = %(weekday_0)s AND business_hour.start_time <= %(end_time_0)s AND business_hour.end_time >= %(start_time_0)s)'  # noqa
                ''
                ' ORDER BY id',
            fetch='all', **self.params,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_no_time_range(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = self.raw_business_hour

        result = await business_hour.browse(
            place_id=self.place_id,
            place_type=self.place_type,
        )

        self.assertEqual(result, self.business_hour)
        mock_init.assert_called_with(
            sql='SELECT id, place_id, type, weekday, start_time, end_time'
                '  FROM business_hour'
                ' WHERE type = %(place_type)s'
                ' AND place_id = %(place_id)s'
                ' ORDER BY id',
            fetch='all', **self.params_no_time_range,
        )
