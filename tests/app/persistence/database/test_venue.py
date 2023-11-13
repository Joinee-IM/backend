from unittest.mock import patch

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
        }

        self.raw_venue = [
            (1, 1, 'name', 'floor', 1, True, True, 1, 'PER_HOUR', 1, 1, 1, 'equipment', 'facility', 1, '場', 1),
            (2, 2, 'name2', 'floor2', 2, False, False, 2, 'PER_PERSON', 2, 2, 2, 'equipment1', 'facility1', 2, '場', 2),
        ]

        self.venues = [
            do.Venue(
                id=1,
                stadium_id=1,
                name='name',
                floor='floor',
                reservation_interval=1,
                is_reservable=True,
                area=1,
                capability=1,
                current_user_count=1,
                court_count=1,
                court_type='場',
                is_chargeable=True,
                sport_id=1,
                fee_rate=1,
                fee_type=enums.FeeType.per_hour,
                sport_equipments='equipment',
                facilities='facility',
            ),
            do.Venue(
                id=2,
                stadium_id=2,
                name='name2',
                floor='floor2',
                reservation_interval=2,
                is_reservable=False,
                area=2,
                capability=2,
                current_user_count=2,
                court_count=2,
                court_type='場',
                is_chargeable=False,
                sport_id=2,
                fee_rate=2,
                fee_type=enums.FeeType.per_person,
                sport_equipments='equipment1',
                facilities='facility1',
            ),
        ]

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = self.raw_venue

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
        mock_init.assert_called_with(
            sql=fr'SELECT id, stadium_id, name, floor, reservation_interval, is_reservable,'
                fr'       is_chargeable, fee_rate, fee_type, area, current_user_count, capability,'
                fr'       sport_equipments, facilities, court_count, court_type, sport_id'
                fr'  FROM venue'
                fr' WHERE name LIKE %(name)s AND sport_id = %(sport_id)s AND is_reservable = %(is_reservable)s'
                fr' ORDER BY current_user_count DESC, venue.id'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            limit=self.limit, offset=self.offset, fetch='all', **self.params,
        )
