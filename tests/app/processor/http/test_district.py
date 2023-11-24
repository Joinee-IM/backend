from unittest.mock import patch

from app.base import do
from app.processor.http import district
from app.utils import Response
from tests import AsyncMock, AsyncTestCase


class TestBrowseDistrict(AsyncTestCase):
    def setUp(self) -> None:
        self.city_id = 1
        self.districts = [
            do.District(
                id=1,
                name='district1',
                city_id=1,
            ),
            do.District(
                id=2,
                name='district2',
                city_id=1,
            ),
        ]
        self.expect_result = Response(data=self.districts)

    @patch('app.persistence.database.district.browse', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock):
        mock_browse.return_value = self.districts

        result = await district.browse_district(city_id=self.city_id)

        self.assertEqual(result, self.expect_result)
        mock_browse.assert_called_with(city_id=self.city_id)
