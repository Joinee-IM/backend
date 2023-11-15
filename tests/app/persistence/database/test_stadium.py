from datetime import time
from unittest.mock import patch

from app.base import do, enums, vo
from app.persistence.database import stadium
from tests import AsyncMock, AsyncTestCase, Mock


class TestBrowse(AsyncTestCase):
    def setUp(self) -> None:
        self.name = 'name'
        self.city_id = 1
        self.district_id = 1
        self.sport_id = 1
        self.limit = 5
        self.offset = 10
        self.params = {
            'name': self.name,
            'city_id': self.city_id,
            'district_id': self.district_id,
            'sport_id': self.sport_id,
        }
        self.query_params = self.params.copy()
        self.query_params['name'] = f'%{self.params["name"]}%'
        self.raw_stadium = [
            (1, 'name', 1, '0800092000', 'desc', 3.14, 1.59, 'city1', 'district1', ['sport1'], [(1, 1, 'STADIUM', 1, time(10, 27), time(20, 27))]),
            (2, 'name2', 2, '0800092001', 'desc2', 3.15, 1.58, 'city2', 'district2', ['sport2'], [(2, 1, 'STADIUM', 1, time(10, 27), time(20, 27))]),
        ]
        self.stadiums = [
            vo.ViewStadium(
                id=1,
                name='name',
                district_id=1,
                contact_number='0800092000',
                description='desc',
                long=3.14,
                lat=1.59,
                city='city1',
                district='district1',
                sports=['sport1'],
                business_hours=[
                    do.BusinessHour(
                        id=1,
                        place_id=1,
                        type=enums.PlaceType.stadium,
                        weekday=1,
                        start_time=time(10, 27),
                        end_time=time(20, 27),
                    )
                ]
            ),
            vo.ViewStadium(
                id=2,
                name='name2',
                district_id=2,
                contact_number='0800092001',
                description='desc2',
                long=3.15,
                lat=1.58,
                city='city2',
                district='district2',
                sports=['sport2'],
                business_hours=[
                    do.BusinessHour(
                        id=2,
                        place_id=1,
                        type=enums.PlaceType.stadium,
                        weekday=1,
                        start_time=time(10, 27),
                        end_time=time(20, 27),
                    )
                ]
            ),
        ]

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = self.raw_stadium

        result = await stadium.browse(
            name=self.name,
            city_id=self.city_id,
            district_id=self.district_id,
            sport_id=self.sport_id,
            limit=self.limit,
            offset=self.offset,
        )

        self.assertEqual(result, self.stadiums)
        mock_init.assert_called_with(
            sql=fr'SELECT stadium.id, stadium.name, district_id, contact_number,'
                fr'       description, long, lat,'
                fr'       city.name,'
                fr'       district.name,'
                fr'       array_agg(sport.name),'
                fr'       array_agg(business_hour.*)'
                fr'  FROM stadium'
                fr' INNER JOIN district ON stadium.district_id = district.id'
                fr' INNER JOIN city ON district.city_id = city.id'
                fr' INNER JOIN venue ON stadium.id = venue.stadium_id'
                fr' INNER JOIN sport ON venue.sport_id = sport.id'
                fr' INNER JOIN business_hour ON business_hour.place_id = stadium.id'
                fr'                         AND business_hour.type = %(place_type)s'
                fr' WHERE stadium.name LIKE %(name)s AND district.city_id = %(city_id)s AND district.id = %(district_id)s AND venue.sport_id = %(sport_id)s'  # noqa
                fr' GROUP BY stadium.id, city.id, district.id'
                fr' ORDER BY stadium.id'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            limit=self.limit, offset=self.offset, place_type=enums.PlaceType.stadium, fetch='all', **self.query_params,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.execute', new_callable=AsyncMock)
    async def test_no_where_sql(self, mock_execute: AsyncMock, mock_init: Mock):
        mock_execute.return_value = self.raw_stadium

        result = await stadium.browse()

        self.assertEqual(result, self.stadiums)
        mock_init.assert_called_with(
            sql=fr'SELECT stadium.id, stadium.name, district_id, contact_number,'
                fr'       description, long, lat,'
                fr'       city.name,'
                fr'       district.name,'
                fr'       array_agg(sport.name),'
                fr'       array_agg(business_hour.*)'
                fr'  FROM stadium'
                fr' INNER JOIN district ON stadium.district_id = district.id'
                fr' INNER JOIN city ON district.city_id = city.id'
                fr' INNER JOIN venue ON stadium.id = venue.stadium_id'
                fr' INNER JOIN sport ON venue.sport_id = sport.id'
                fr' INNER JOIN business_hour ON business_hour.place_id = stadium.id'
                fr'                         AND business_hour.type = %(place_type)s'
                fr' '
                fr' GROUP BY stadium.id, city.id, district.id'
                fr' ORDER BY stadium.id'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            limit=10, offset=0, place_type=enums.PlaceType.stadium, fetch='all',
        )
