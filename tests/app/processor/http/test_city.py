from unittest.mock import patch

from app.base import do
from app.processor.http import city
from app.utils import Response
from tests import AsyncMock, AsyncTestCase


class TestBrowseCity(AsyncTestCase):
    def setUp(self) -> None:
        self.cities = [
            do.City(
                id=1,
                name='city1',
            ),
            do.City(
                id=2,
                name='city2',
            ),
        ]
        self.expect_result = Response(data=self.cities)

    @patch('app.persistence.database.city.browse', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock):
        mock_browse.return_value = self.cities

        result = await city.browse_city()

        self.assertEqual(result, self.expect_result)
        mock_browse.assert_called()
