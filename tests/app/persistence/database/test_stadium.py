from datetime import time
from unittest.mock import call, patch

import app.exceptions as exc
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
            'weekday_0': 1,
            'start_time_0': time(10, 27),
            'end_time_0': time(17, 27),
            'is_published': True,
        }
        self.time_ranges = [
            vo.WeekTimeRange(
                weekday=1,
                start_time=time(10, 27),
                end_time=time(17, 27),
            ),
        ]
        self.query_params = self.params.copy()
        self.query_params['name'] = f'%{self.params["name"]}%'
        self.no_filter_params = {'is_published': True}
        self.raw_stadium = [
            (1, 'name', 1, '0800092000', 1, 'address1', 'desc', 3.14, 1.59, True, 'city1', 'district1', ['sport1'], [(1, 1, 'STADIUM', 1, time(10, 27), time(20, 27))]),
            (2, 'name2', 2, '0800092001', 2, 'address2', 'desc2', 3.15, 1.58, True, 'city2', 'district2', ['sport2'], [(2, 1, 'STADIUM', 1, time(10, 27), time(20, 27))]),
        ]
        self.total_count = 1
        self.stadiums = [
            vo.ViewStadium(
                id=1,
                name='name',
                district_id=1,
                contact_number='0800092000',
                description='desc',
                owner_id=1,
                address='address1',
                long=3.14,
                lat=1.59,
                is_published=True,
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
                    ),
                ],
            ),
            vo.ViewStadium(
                id=2,
                name='name2',
                district_id=2,
                contact_number='0800092001',
                description='desc2',
                owner_id=2,
                address='address2',
                long=3.15,
                lat=1.58,
                is_published=True,
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
                    ),
                ],
            ),
        ], self.total_count

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_fetch_all: AsyncMock, mock_init: Mock):
        mock_fetch_all.return_value = self.raw_stadium
        mock_fetch.return_value = self.total_count,

        result = await stadium.browse(
            name=self.name,
            city_id=self.city_id,
            district_id=self.district_id,
            sport_id=self.sport_id,
            limit=self.limit,
            offset=self.offset,
            time_ranges=self.time_ranges,
        )

        self.assertEqual(result, self.stadiums)
        mock_init.assert_has_calls([
            call(
                sql=r'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id, address,'
                    r'       description, long, lat, stadium.is_published,'
                    r'       city.name,'
                    r'       district.name,'
                    r'       ARRAY_AGG(DISTINCT sport.name) AS sport_names,'
                    r'       ARRAY_AGG(DISTINCT business_hour.*) AS business_hour'
                    r'  FROM stadium'
                    r' INNER JOIN ('
                    r'     SELECT stadium.id AS stadium_id'
                    r'       FROM stadium'
                    r'      INNER JOIN district ON stadium.district_id = district.id'
                    r'      INNER JOIN city ON district.city_id = city.id'
                    r'       LEFT JOIN venue ON stadium.id = venue.stadium_id'
                    r'       LEFT JOIN sport ON venue.sport_id = sport.id'
                    r'       LEFT JOIN business_hour ON business_hour.place_id = stadium.id'
                    r'             AND business_hour.type = %(place_type)s'
                    r' WHERE stadium.name LIKE %(name)s'
                    r' AND district.city_id = %(city_id)s'
                    r' AND district.id = %(district_id)s'
                    r' AND venue.sport_id = %(sport_id)s'
                    r' AND stadium.is_published = %(is_published)s'
                    r' AND ((business_hour.weekday = %(weekday_0)s'
                    r' AND business_hour.start_time < %(end_time_0)s'
                    r' AND business_hour.end_time > %(start_time_0)s))'
                    r'        GROUP BY stadium.id, city.id, district.id'
                    r'   ) tbl ON tbl.stadium_id = stadium.id'
                    r' INNER JOIN district ON stadium.district_id = district.id'
                    r' INNER JOIN city ON district.city_id = city.id'
                    r'  LEFT JOIN venue ON stadium.id = venue.stadium_id'
                    r'  LEFT JOIN sport ON venue.sport_id = sport.id'
                    r'  LEFT JOIN business_hour ON business_hour.place_id = stadium.id'
                    r'                         AND business_hour.type = %(place_type)s'
                    r' GROUP BY stadium.id, city.id, district.id'
                    r' ORDER BY stadium.id'
                    r' LIMIT %(limit)s OFFSET %(offset)s',
                limit=self.limit, offset=self.offset, place_type=enums.PlaceType.stadium,
                **self.query_params,
            ),
            call(
                sql=r'SELECT COUNT(*)'
                    r'  FROM ('
                    r'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id, address,'
                    r'       description, long, lat, stadium.is_published,'
                    r'       city.name,'
                    r'       district.name,'
                    r'       ARRAY_AGG(DISTINCT sport.name) AS sport_names,'
                    r'       ARRAY_AGG(DISTINCT business_hour.*) AS business_hour'
                    r'  FROM stadium'
                    r' INNER JOIN ('
                    r'     SELECT stadium.id AS stadium_id'
                    r'       FROM stadium'
                    r'      INNER JOIN district ON stadium.district_id = district.id'
                    r'      INNER JOIN city ON district.city_id = city.id'
                    r'       LEFT JOIN venue ON stadium.id = venue.stadium_id'
                    r'       LEFT JOIN sport ON venue.sport_id = sport.id'
                    r'       LEFT JOIN business_hour ON business_hour.place_id = stadium.id'
                    r'             AND business_hour.type = %(place_type)s'
                    r' WHERE stadium.name LIKE %(name)s'
                    r' AND district.city_id = %(city_id)s'
                    r' AND district.id = %(district_id)s'
                    r' AND venue.sport_id = %(sport_id)s'
                    r' AND stadium.is_published = %(is_published)s'
                    r' AND ((business_hour.weekday = %(weekday_0)s'
                    r' AND business_hour.start_time < %(end_time_0)s'
                    r' AND business_hour.end_time > %(start_time_0)s))'
                    r'        GROUP BY stadium.id, city.id, district.id'
                    r'   ) tbl ON tbl.stadium_id = stadium.id'
                    r' INNER JOIN district ON stadium.district_id = district.id'
                    r' INNER JOIN city ON district.city_id = city.id'
                    r'  LEFT JOIN venue ON stadium.id = venue.stadium_id'
                    r'  LEFT JOIN sport ON venue.sport_id = sport.id'
                    r'  LEFT JOIN business_hour ON business_hour.place_id = stadium.id'
                    r'                         AND business_hour.type = %(place_type)s'
                    r' GROUP BY stadium.id, city.id, district.id) AS tbl',
                place_type=enums.PlaceType.stadium,
                **self.query_params,
            ),
        ])

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_no_filter(self, mock_fetch: AsyncMock, mock_fetch_all: AsyncMock, mock_init: Mock):
        mock_fetch_all.return_value = self.raw_stadium
        mock_fetch.return_value = self.total_count,
        result = await stadium.browse()

        self.assertEqual(result, self.stadiums)
        mock_init.assert_has_calls([
            call(
                sql=r'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id, address,'
                    r'       description, long, lat, stadium.is_published,'
                    r'       city.name,'
                    r'       district.name,'
                    r'       ARRAY_AGG(DISTINCT sport.name) AS sport_names,'
                    r'       ARRAY_AGG(DISTINCT business_hour.*) AS business_hour'
                    r'  FROM stadium'
                    r' INNER JOIN ('
                    r'     SELECT stadium.id AS stadium_id'
                    r'       FROM stadium'
                    r'      INNER JOIN district ON stadium.district_id = district.id'
                    r'      INNER JOIN city ON district.city_id = city.id'
                    r'       LEFT JOIN venue ON stadium.id = venue.stadium_id'
                    r'       LEFT JOIN sport ON venue.sport_id = sport.id'
                    r'       LEFT JOIN business_hour ON business_hour.place_id = stadium.id'
                    r'             AND business_hour.type = %(place_type)s'
                    r' WHERE stadium.is_published = %(is_published)s'
                    r'        GROUP BY stadium.id, city.id, district.id'
                    r'   ) tbl ON tbl.stadium_id = stadium.id'
                    r' INNER JOIN district ON stadium.district_id = district.id'
                    r' INNER JOIN city ON district.city_id = city.id'
                    r'  LEFT JOIN venue ON stadium.id = venue.stadium_id'
                    r'  LEFT JOIN sport ON venue.sport_id = sport.id'
                    r'  LEFT JOIN business_hour ON business_hour.place_id = stadium.id'
                    r'                         AND business_hour.type = %(place_type)s'
                    r' GROUP BY stadium.id, city.id, district.id'
                    r' ORDER BY stadium.id'
                    r' LIMIT %(limit)s OFFSET %(offset)s',
                limit=10, offset=0, place_type=enums.PlaceType.stadium, **self.no_filter_params,
            ),
            call(
                sql=r'SELECT COUNT(*)'
                    r'  FROM ('
                    r'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id, address,'
                    r'       description, long, lat, stadium.is_published,'
                    r'       city.name,'
                    r'       district.name,'
                    r'       ARRAY_AGG(DISTINCT sport.name) AS sport_names,'
                    r'       ARRAY_AGG(DISTINCT business_hour.*) AS business_hour'
                    r'  FROM stadium'
                    r' INNER JOIN ('
                    r'     SELECT stadium.id AS stadium_id'
                    r'       FROM stadium'
                    r'      INNER JOIN district ON stadium.district_id = district.id'
                    r'      INNER JOIN city ON district.city_id = city.id'
                    r'       LEFT JOIN venue ON stadium.id = venue.stadium_id'
                    r'       LEFT JOIN sport ON venue.sport_id = sport.id'
                    r'       LEFT JOIN business_hour ON business_hour.place_id = stadium.id'
                    r'             AND business_hour.type = %(place_type)s'
                    r' WHERE stadium.is_published = %(is_published)s'
                    r'        GROUP BY stadium.id, city.id, district.id'
                    r'   ) tbl ON tbl.stadium_id = stadium.id'
                    r' INNER JOIN district ON stadium.district_id = district.id'
                    r' INNER JOIN city ON district.city_id = city.id'
                    r'  LEFT JOIN venue ON stadium.id = venue.stadium_id'
                    r'  LEFT JOIN sport ON venue.sport_id = sport.id'
                    r'  LEFT JOIN business_hour ON business_hour.place_id = stadium.id'
                    r'                         AND business_hour.type = %(place_type)s'
                    r' GROUP BY stadium.id, city.id, district.id) AS tbl',
                place_type=enums.PlaceType.stadium, **self.no_filter_params,
            ),
        ])


class TestRead(AsyncTestCase):
    def setUp(self) -> None:
        self.stadium_id = 1
        self.raw_stadium = (1, 'name', 1, '0800092000', 1, 'address', 'desc', 3.14, 1.59, True, 'city1', 'district1', ['sport1'], [(1, 1, 'STADIUM', 1, time(10, 27), time(20, 27))])
        self.stadium = vo.ViewStadium(
            id=1,
            name='name',
            district_id=1,
            contact_number='0800092000',
            description='desc',
            owner_id=1,
            address='address',
            long=3.14,
            lat=1.59,
            is_published=True,
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
                ),
            ],
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_stadium

        result = await stadium.read(stadium_id=self.stadium_id)

        self.assertEqual(result, self.stadium)
        mock_init.assert_called_with(
            sql=r'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id, address,'
                r'       description, long, lat, stadium.is_published,'
                r'       city.name,'
                r'       district.name,'
                r'       ARRAY_AGG(DISTINCT sport.name),'
                r'       ARRAY_AGG(DISTINCT business_hour.*)'
                r'  FROM stadium'
                r' INNER JOIN district ON stadium.district_id = district.id'
                r' INNER JOIN city ON district.city_id = city.id'
                r'  LEFT JOIN venue ON stadium.id = venue.stadium_id'
                r'  LEFT JOIN sport ON venue.sport_id = sport.id'
                r'  LEFT JOIN business_hour ON business_hour.place_id = stadium.id'
                r'                         AND business_hour.type = %(place_type)s'
                r' WHERE stadium.id = %(stadium_id)s'
                r' AND stadium.is_published = True'
                r' GROUP BY stadium.id, city.id, district.id'
                r' ORDER BY stadium.id',
            place_type=enums.PlaceType.stadium, stadium_id=self.stadium_id,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_not_found(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = None

        with self.assertRaises(exc.NotFound):
            await stadium.read(stadium_id=self.stadium_id)

        mock_init.assert_called_with(
            sql=r'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id, address,'
                r'       description, long, lat, stadium.is_published,'
                r'       city.name,'
                r'       district.name,'
                r'       ARRAY_AGG(DISTINCT sport.name),'
                r'       ARRAY_AGG(DISTINCT business_hour.*)'
                r'  FROM stadium'
                r' INNER JOIN district ON stadium.district_id = district.id'
                r' INNER JOIN city ON district.city_id = city.id'
                r'  LEFT JOIN venue ON stadium.id = venue.stadium_id'
                r'  LEFT JOIN sport ON venue.sport_id = sport.id'
                r'  LEFT JOIN business_hour ON business_hour.place_id = stadium.id'
                r'                         AND business_hour.type = %(place_type)s'
                r' WHERE stadium.id = %(stadium_id)s'
                r' AND stadium.is_published = True'
                r' GROUP BY stadium.id, city.id, district.id'
                r' ORDER BY stadium.id',
            place_type=enums.PlaceType.stadium, stadium_id=self.stadium_id,
        )


class TestAdd(AsyncTestCase):
    def setUp(self) -> None:
        self.stadium_id = 1
        self.name = 'stadium'
        self.address = '台北市大安區羅斯福路四段1號'
        self.district_id = 1
        self.owner_id = 1
        self.contact_number = '0800000000'
        self.description = 'desc'
        self.long = 121.5397518
        self.lat = 25.0173405

        self.expect_result = self.stadium_id

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch, mock_init):
        mock_fetch.return_value = 1,

        result = await stadium.add(
           name=self.name, address=self.address, district_id=self.district_id, owner_id=self.owner_id,
           contact_number=self.contact_number, description=self.description, long=self.long, lat=self.lat,
        )

        self.assertEqual(result, self.expect_result)
        mock_init.assert_called_with(
            sql=r'INSERT INTO stadium(name, district_id, owner_id, address, contact_number, description, long,'
                r'                        lat, is_published)'
                r'                 VALUES(%(name)s, %(district_id)s, %(owner_id)s, %(address)s, %(contact_number)s,'
                r'                        %(description)s, %(long)s, %(lat)s, %(is_published)s)'
                r'  RETURNING id',
            name=self.name, district_id=self.district_id, owner_id=self.owner_id, address=self.address,
            contact_number=self.contact_number, description=self.description, long=self.long, lat=self.lat, is_published=True,
        )
