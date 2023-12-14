from unittest.mock import patch

from app.base import do
from app.persistence.database import city
from tests import AsyncMock, AsyncTestCase, Mock


class TestBrowse(AsyncTestCase):
    def setUp(self) -> None:
        self.raw_city = [
            (1, '台北市'),
            (2, '新北市'),
        ]
        self.cities = [
            do.City(
                id=1,
                name='台北市',
            ),
            do.City(
                id=2,
                name='新北市',
            ),
        ]

    @patch('app.persistence.database.util.PostgresQueryExecutor.__init__', new_callable=Mock)
    @patch('app.persistence.database.util.PostgresQueryExecutor.fetch_all', new_callable=AsyncMock)
    async def test_happy_path(self, mock_fetch: AsyncMock, mock_init: Mock):
        mock_fetch.return_value = self.raw_city

        result = await city.browse()

        self.assertEqual(result, self.cities)
        mock_init.assert_called_with(
            sql=r'SELECT city.id, city.name'
                r'  FROM city',
        )
