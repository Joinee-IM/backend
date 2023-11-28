from unittest.mock import patch

from app.base import do
from app.persistence.database import district
from tests import AsyncMock, AsyncTestCase, Mock


class TestBrowse(AsyncTestCase):
    def setUp(self) -> None:
        self.city_id = 1
        self.raw_district = [
            (1, '大安區', 1),
            (2, '信義區', 1),
        ]
        self.districts = [
            do.District(
                id=1,
                name='大安區',
                city_id=1
            ),
            do.District(
                id=2,
                name='信義區',
                city_id=1
            ),
        ]

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_district

        result = await district.browse(city_id=self.city_id)

        self.assertEqual(result, self.districts)
        mock_init.assert_called_with(
            sql=r'SELECT district.id, district.name, district.city_id'
                r'  FROM district'
                r' WHERE district.city_id = %(city_id)s',
            city_id=self.city_id,
        )
