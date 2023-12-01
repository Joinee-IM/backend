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
                sql=fr'SELECT id, stadium_id, name, floor, reservation_interval, is_reservable,'
                    fr'       is_chargeable, fee_rate, fee_type, area, current_user_count, capacity,'
                    fr'       sport_equipments, facilities, court_count, court_type, sport_id, is_published'
                    fr'  FROM venue'
                    fr' WHERE name LIKE %(name)s AND sport_id = %(sport_id)s AND is_reservable = %(is_reservable)s'
                    fr' AND is_published = %(is_published)s'
                    fr' ORDER BY current_user_count DESC, venue.id'
                    fr' LIMIT %(limit)s OFFSET %(offset)s',
                limit=self.limit, offset=self.offset, **self.params,
            ),
            call(
                sql=fr'SELECT COUNT(*)'
                    fr'  FROM ('
                    fr'SELECT id, stadium_id, name, floor, reservation_interval, is_reservable,'
                    fr'       is_chargeable, fee_rate, fee_type, area, current_user_count, capacity,'
                    fr'       sport_equipments, facilities, court_count, court_type, sport_id, is_published'
                    fr'  FROM venue'
                    fr' WHERE name LIKE %(name)s AND sport_id = %(sport_id)s AND is_reservable = %(is_reservable)s'
                    fr' AND is_published = %(is_published)s'
                    fr' ORDER BY current_user_count DESC, venue.id) AS tbl',
                **self.params,
            )
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
            sql=fr'SELECT id, stadium_id, name, floor, reservation_interval, is_reservable,'
                fr'       is_chargeable, fee_rate, fee_type, area, current_user_count, capacity,'
                fr'       sport_equipments, facilities, court_count, court_type, sport_id, is_published'
                fr'  FROM venue'
                fr' WHERE venue.id = %(venue_id)s'
                fr' AND is_published',
            venue_id=self.venue_id,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_not_found(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = None

        with self.assertRaises(exc.NotFound):
            await venue.read(venue_id=self.venue_id)

        mock_init.assert_called_with(
            sql=fr'SELECT id, stadium_id, name, floor, reservation_interval, is_reservable,'
                fr'       is_chargeable, fee_rate, fee_type, area, current_user_count, capacity,'
                fr'       sport_equipments, facilities, court_count, court_type, sport_id, is_published'
                fr'  FROM venue'
                fr' WHERE venue.id = %(venue_id)s'
                fr' AND is_published',
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
