from unittest.mock import call, patch

import app.exceptions as exc
from app.base import do, enums
from app.persistence.database import venue
from tests import AsyncMock, AsyncTestCase, Mock


class TestBrowse(AsyncTestCase):
    def setUp(self) -> None:
        self.name = 'name'
        self.sport_id = 1
        self.is_reservable = True
        self.sort_by = enums.VenueAvailableSortBy.current_user_count
        self.order = enums.Sorter.desc
        self.limit = 10
        self.offset = 0

        self.params = {
            'name': f'%{self.name}%',
            'sport_id': self.sport_id,
            'is_reservable': self.is_reservable,
            'is_published': True,
        }

        self.raw_venue = [
            (1, 1, 'name', 'floor', 1, True, True, 1, 'PER_HOUR', 1, 1, 1, 'equipment', 'facility', 1, '場', 1, True),
            (2, 2, 'name2', 'floor2', 2, False, False, 2, 'PER_PERSON', 2, 2, 2, 'equipment1', 'facility1', 2, '場', 2, True),
        ]
        self.total_count = 1

        self.venues = [
            do.Venue(
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
            ),
            do.Venue(
                id=2,
                stadium_id=2,
                name='name2',
                floor='floor2',
                reservation_interval=2,
                is_reservable=False,
                area=2,
                capacity=2,
                current_user_count=2,
                court_count=2,
                court_type='場',
                is_chargeable=False,
                sport_id=2,
                fee_rate=2,
                fee_type=enums.FeeType.per_person,
                sport_equipments='equipment1',
                facilities='facility1',
                is_published=True,
            ),
        ], self.total_count

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_fetch_all: AsyncMock, mock_init: Mock):
        mock_fetch_all.return_value = self.raw_venue
        mock_fetch.return_value = self.total_count,
        result = await venue.browse(
            name=self.name,
            sport_id=self.sport_id,
            is_reservable=self.is_reservable,
            sort_by=self.sort_by,
            order=self.order,
            limit=self.limit,
            offset=self.offset,
        )

        self.assertEqual(result, self.venues)
        mock_init.assert_has_calls([
            call(
                sql=r'SELECT venue.id, stadium_id, name, floor, reservation_interval, is_reservable,'
                    r'       is_chargeable, fee_rate, fee_type, area, current_user_count, capacity,'
                    r'       sport_equipments, facilities, COUNT(court.*) AS court_count, court_type, sport_id, venue.is_published'  # noqa
                    r'  FROM venue'
                    r'  LEFT JOIN court ON court.venue_id = venue.id'
                    r' WHERE name LIKE %(name)s AND sport_id = %(sport_id)s AND is_reservable = %(is_reservable)s'
                    r' AND venue.is_published = %(is_published)s'
                    r' AND court.is_published = %(is_published)s'
                    r' GROUP BY venue.id'
                    r' ORDER BY current_user_count DESC, venue.id'
                    r' LIMIT %(limit)s OFFSET %(offset)s',
                limit=self.limit, offset=self.offset, **self.params,
            ),
            call(
                sql=r'SELECT COUNT(*)'
                    r'  FROM ('
                    r'SELECT venue.id, stadium_id, name, floor, reservation_interval, is_reservable,'
                    r'       is_chargeable, fee_rate, fee_type, area, current_user_count, capacity,'
                    r'       sport_equipments, facilities, COUNT(court.*) AS court_count, court_type, sport_id, venue.is_published'  # noqa
                    r'  FROM venue'
                    r'  LEFT JOIN court ON court.venue_id = venue.id'
                    r' WHERE name LIKE %(name)s AND sport_id = %(sport_id)s AND is_reservable = %(is_reservable)s'
                    r' AND venue.is_published = %(is_published)s'
                    r' AND court.is_published = %(is_published)s'
                    r' GROUP BY venue.id) AS tbl',
                **self.params,
            ),
        ])


class TestRead(AsyncTestCase):
    def setUp(self) -> None:
        self.venue_id = 1
        self.raw_venue = (1, 1, 'name', 'floor', 1, True, True, 1, 'PER_HOUR', 1, 1, 1, 'equipment', 'facility', 1, '場', 1, True)
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

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_venue

        result = await venue.read(venue_id=self.venue_id)

        self.assertEqual(result, self.venue)
        mock_init.assert_called_with(
            sql=r'SELECT venue.id, stadium_id, name, floor, reservation_interval, is_reservable,'
                r'       is_chargeable, fee_rate, fee_type, area, current_user_count, capacity,'
                r'       sport_equipments, facilities, COUNT(court.*) AS court_count, '
                r'       court_type, sport_id, venue.is_published'
                r'  FROM venue'
                r'  LEFT JOIN court ON court.venue_id = venue.id'
                r' WHERE venue.id = %(venue_id)s'
                r' AND venue.is_published'
                r' AND court.is_published'
                r' GROUP BY venue.id',
            venue_id=self.venue_id,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_not_found(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = None

        with self.assertRaises(exc.NotFound):
            await venue.read(venue_id=self.venue_id)

        mock_init.assert_called_with(
            sql=r'SELECT venue.id, stadium_id, name, floor, reservation_interval, is_reservable,'
                r'       is_chargeable, fee_rate, fee_type, area, current_user_count, capacity,'
                r'       sport_equipments, facilities, COUNT(court.*) AS court_count, '
                r'       court_type, sport_id, venue.is_published'
                r'  FROM venue'
                r'  LEFT JOIN court ON court.venue_id = venue.id'
                r' WHERE venue.id = %(venue_id)s'
                r' AND venue.is_published'
                r' AND court.is_published'
                r' GROUP BY venue.id',
            venue_id=self.venue_id,
        )


class TestEdit(AsyncTestCase):
    def setUp(self) -> None:
        self.venue_id = 1
        self.name = 'name'
        self.floor = 'f'
        self.area = 1
        self.capacity = 1
        self.sport_id = 1
        self.is_reservable = True
        self.reservation_interval = 1
        self.is_chargeable = True
        self.fee_rate = 0.1
        self.fee_type = enums.FeeType.per_hour
        self.sport_equipments = 'se'
        self.facilities = 'f'
        self.court_type = 'ct'

    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock):
        result = await venue.edit(
            venue_id=self.venue_id,
            name=self.name,
            floor=self.floor,
            area=self.area,
            capacity=self.capacity,
            sport_id=self.sport_id,
            is_reservable=self.is_reservable,
            reservation_interval=self.reservation_interval,
            is_chargeable=self.is_chargeable,
            fee_rate=self.fee_rate,
            fee_type=self.fee_type,
            sport_equipments=self.sport_equipments,
            facilities=self.facilities,
            court_type=self.court_type,
        )
        self.assertIsNone(result)
        mock_execute.assert_called_once()


class TestAdd(AsyncTestCase):
    def setUp(self) -> None:
        self.stadium_id = 1
        self.name = '桌球室'
        self.floor = '4'
        self.reservation_interval = 3
        self.is_reservable = True
        self.is_chargeable = True
        self.fee_rate = 300
        self.fee_type = enums.FeeType.per_hour
        self.area = 600
        self.capacity = 1000
        self.sport_equipments = '桌球拍'
        self.facilities = '吹風機'
        self.court_count = 5
        self.court_type = '桌'
        self.sport_id = 1

        self.venue_id = 1

        self.expect_result = self.venue_id

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch, mock_init):
        mock_fetch.return_value = 1,

        result = await venue.add(
            stadium_id=self.stadium_id, name=self.name, floor=self.floor, reservation_interval=self.reservation_interval,
            is_reservable=self.is_reservable, is_chargeable=self.is_chargeable, fee_rate=self.fee_rate,
            fee_type=self.fee_type, area=self.area, capacity=self.capacity, sport_equipments=self.sport_equipments,
            facilities=self.facilities, court_count=self.court_count, court_type=self.court_type, sport_id=self.sport_id,
        )

        self.assertEqual(result, self.expect_result)
        mock_init.assert_called_with(
            sql=r'INSERT INTO venue'
                r'            (stadium_id, name, floor, reservation_interval, is_reservable, is_chargeable, fee_rate,'
                r'             fee_type, area, capacity, sport_equipments, facilities, court_count, court_type, sport_id, is_published)'
                r'     VALUES (%(stadium_id)s, %(name)s, %(floor)s, %(reservation_interval)s, %(is_reservable)s,'
                r'            %(is_chargeable)s, %(fee_rate)s, %(fee_type)s, %(area)s, %(capacity)s,'
                r'            %(sport_equipments)s, %(facilities)s, %(court_count)s, %(court_type)s, %(sport_id)s,'
                r'            %(is_published)s)'
                r'  RETURNING id',
            stadium_id=self.stadium_id, name=self.name, floor=self.floor, reservation_interval=self.reservation_interval,
            is_reservable=self.is_reservable,
            is_chargeable=self.is_chargeable, fee_rate=self.fee_rate, fee_type=self.fee_type, area=self.area,
            capacity=self.capacity, sport_equipments=self.sport_equipments,
            facilities=self.facilities, court_count=self.court_count, court_type=self.court_type, sport_id=self.sport_id,
            is_published=True,
        )
