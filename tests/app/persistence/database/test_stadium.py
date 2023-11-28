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
            (1, 'name', 1, '0800092000', 1, 'desc', 3.14, 1.59, True, 'city1', 'district1', ['sport1'], [(1, 1, 'STADIUM', 1, time(10, 27), time(20, 27))]),
            (2, 'name2', 2, '0800092001', 2, 'desc2', 3.15, 1.58, True, 'city2', 'district2', ['sport2'], [(2, 1, 'STADIUM', 1, time(10, 27), time(20, 27))]),
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
                    )
                ]
            ),
            vo.ViewStadium(
                id=2,
                name='name2',
                district_id=2,
                contact_number='0800092001',
                description='desc2',
                owner_id=2,
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
                    )
                ]
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
                sql=fr'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id,'
                    fr'       description, long, lat, stadium.is_published,'
                    fr'       city.name,'
                    fr'       district.name,'
                    fr'       ARRAY_AGG(DISTINCT sport.name),'
                    fr'       ARRAY_AGG(DISTINCT business_hour.*)'
                    fr'  FROM stadium'
                    fr' INNER JOIN district ON stadium.district_id = district.id'
                    fr' INNER JOIN city ON district.city_id = city.id'
                    fr'  LEFT JOIN venue ON stadium.id = venue.stadium_id'
                    fr'  LEFT JOIN sport ON venue.sport_id = sport.id'
                    fr' INNER JOIN business_hour ON business_hour.place_id = stadium.id'
                    fr'                         AND business_hour.type = %(place_type)s'
                    fr' WHERE stadium.name LIKE %(name)s'
                    fr' AND district.city_id = %(city_id)s'
                    fr' AND district.id = %(district_id)s'
                    fr' AND venue.sport_id = %(sport_id)s'
                    fr' AND stadium.is_published = %(is_published)s'
                    fr' AND (business_hour.weekday = %(weekday_0)s'
                    fr' AND business_hour.start_time <= %(end_time_0)s'
                    fr' AND business_hour.end_time >= %(start_time_0)s)'
                    fr' GROUP BY stadium.id, city.id, district.id'
                    fr' ORDER BY stadium.id'
                    fr' LIMIT %(limit)s OFFSET %(offset)s',
                limit=self.limit, offset=self.offset, place_type=enums.PlaceType.stadium,
                **self.query_params,
            ),
            call(
                sql=fr'SELECT COUNT(*)'
                    fr'  FROM ('
                    fr'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id,'
                    fr'       description, long, lat, stadium.is_published,'
                    fr'       city.name,'
                    fr'       district.name,'
                    fr'       ARRAY_AGG(DISTINCT sport.name),'
                    fr'       ARRAY_AGG(DISTINCT business_hour.*)'
                    fr'  FROM stadium'
                    fr' INNER JOIN district ON stadium.district_id = district.id'
                    fr' INNER JOIN city ON district.city_id = city.id'
                    fr'  LEFT JOIN venue ON stadium.id = venue.stadium_id'
                    fr'  LEFT JOIN sport ON venue.sport_id = sport.id'
                    fr' INNER JOIN business_hour ON business_hour.place_id = stadium.id'
                    fr'                         AND business_hour.type = %(place_type)s'
                    fr' WHERE stadium.name LIKE %(name)s'
                    fr' AND district.city_id = %(city_id)s'
                    fr' AND district.id = %(district_id)s'
                    fr' AND venue.sport_id = %(sport_id)s'
                    fr' AND stadium.is_published = %(is_published)s'
                    fr' AND (business_hour.weekday = %(weekday_0)s'
                    fr' AND business_hour.start_time <= %(end_time_0)s'
                    fr' AND business_hour.end_time >= %(start_time_0)s)'
                    fr' GROUP BY stadium.id, city.id, district.id'
                    fr' ORDER BY stadium.id) AS tbl',
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
                sql=fr'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id,'
                    fr'       description, long, lat, stadium.is_published,'
                    fr'       city.name,'
                    fr'       district.name,'
                    fr'       ARRAY_AGG(DISTINCT sport.name),'
                    fr'       ARRAY_AGG(DISTINCT business_hour.*)'
                    fr'  FROM stadium'
                    fr' INNER JOIN district ON stadium.district_id = district.id'
                    fr' INNER JOIN city ON district.city_id = city.id'
                    fr'  LEFT JOIN venue ON stadium.id = venue.stadium_id'
                    fr'  LEFT JOIN sport ON venue.sport_id = sport.id'
                    fr' INNER JOIN business_hour ON business_hour.place_id = stadium.id'
                    fr'                         AND business_hour.type = %(place_type)s'
                    fr' WHERE stadium.is_published = %(is_published)s'
                    fr' GROUP BY stadium.id, city.id, district.id'
                    fr' ORDER BY stadium.id'
                    fr' LIMIT %(limit)s OFFSET %(offset)s',
                limit=10, offset=0, place_type=enums.PlaceType.stadium, **self.no_filter_params,
            ),
            call(
                sql=fr'SELECT COUNT(*)'
                    fr'  FROM ('
                    fr'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id,'
                    fr'       description, long, lat, stadium.is_published,'
                    fr'       city.name,'
                    fr'       district.name,'
                    fr'       ARRAY_AGG(DISTINCT sport.name),'
                    fr'       ARRAY_AGG(DISTINCT business_hour.*)'
                    fr'  FROM stadium'
                    fr' INNER JOIN district ON stadium.district_id = district.id'
                    fr' INNER JOIN city ON district.city_id = city.id'
                    fr'  LEFT JOIN venue ON stadium.id = venue.stadium_id'
                    fr'  LEFT JOIN sport ON venue.sport_id = sport.id'
                    fr' INNER JOIN business_hour ON business_hour.place_id = stadium.id'
                    fr'                         AND business_hour.type = %(place_type)s'
                    fr' WHERE stadium.is_published = %(is_published)s'
                    fr' GROUP BY stadium.id, city.id, district.id'
                    fr' ORDER BY stadium.id) AS tbl',
                place_type=enums.PlaceType.stadium, **self.no_filter_params,
            ),
        ])


class TestRead(AsyncTestCase):
    def setUp(self) -> None:
        self.stadium_id = 1
        self.raw_stadium = (1, 'name', 1, '0800092000', 1, 'desc', 3.14, 1.59, True, 'city1', 'district1', ['sport1'], [(1, 1, 'STADIUM', 1, time(10, 27), time(20, 27))])
        self.stadium = vo.ViewStadium(
            id=1,
            name='name',
            district_id=1,
            contact_number='0800092000',
            description='desc',
            owner_id=1,
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
                )
            ]
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_stadium

        result = await stadium.read(stadium_id=self.stadium_id)

        self.assertEqual(result, self.stadium)
        mock_init.assert_called_with(
            sql=fr'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id,'
                fr'       description, long, lat, stadium.is_published,'
                fr'       city.name,'
                fr'       district.name,'
                fr'       ARRAY_AGG(DISTINCT sport.name),'
                fr'       ARRAY_AGG(DISTINCT business_hour.*)'
                fr'  FROM stadium'
                fr' INNER JOIN district ON stadium.district_id = district.id'
                fr' INNER JOIN city ON district.city_id = city.id'
                fr' INNER JOIN venue ON stadium.id = venue.stadium_id'
                fr' INNER JOIN sport ON venue.sport_id = sport.id'
                fr' INNER JOIN business_hour ON business_hour.place_id = stadium.id'
                fr'                         AND business_hour.type = %(place_type)s'
                fr' WHERE stadium.id = %(stadium_id)s'
                fr' AND stadium.is_published = True'
                fr' GROUP BY stadium.id, city.id, district.id'
                fr' ORDER BY stadium.id',
            place_type=enums.PlaceType.stadium, stadium_id=self.stadium_id,
        )

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_one', new_callable=AsyncMock)
    async def test_not_found(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = None

        with self.assertRaises(exc.NotFound):
            await stadium.read(stadium_id=self.stadium_id)

        mock_init.assert_called_with(
            sql=fr'SELECT stadium.id, stadium.name, district_id, contact_number, owner_id,'
                fr'       description, long, lat, stadium.is_published,'
                fr'       city.name,'
                fr'       district.name,'
                fr'       ARRAY_AGG(DISTINCT sport.name),'
                fr'       ARRAY_AGG(DISTINCT business_hour.*)'
                fr'  FROM stadium'
                fr' INNER JOIN district ON stadium.district_id = district.id'
                fr' INNER JOIN city ON district.city_id = city.id'
                fr' INNER JOIN venue ON stadium.id = venue.stadium_id'
                fr' INNER JOIN sport ON venue.sport_id = sport.id'
                fr' INNER JOIN business_hour ON business_hour.place_id = stadium.id'
                fr'                         AND business_hour.type = %(place_type)s'
                fr' WHERE stadium.id = %(stadium_id)s'
                fr' AND stadium.is_published = True'
                fr' GROUP BY stadium.id, city.id, district.id'
                fr' ORDER BY stadium.id',
            place_type=enums.PlaceType.stadium, stadium_id=self.stadium_id,
        )
