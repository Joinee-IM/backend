from unittest.mock import patch

from app.base import do
from app.processor.http import stadium
from app.utils import Response
from tests import AsyncMock, AsyncTestCase


class TestSearchStadium(AsyncTestCase):
    def setUp(self) -> None:
        self.params = stadium.StadiumSearchParameters(
            name='name',
            city_id=1,
            district_id=1,
            sport_id=1,
            limit=1,
            offset=1,
        )
        self.stadiums = [
            do.Stadium(
                id=1,
                name='name',
                district_id=1,
                contact_number='0800092000',
                description='desc',
                long=3.14,
                lat=1.59,
            ),
            do.Stadium(
                id=2,
                name='name2',
                district_id=2,
                contact_number='0800092001',
                description='desc2',
                long=3.15,
                lat=1.58,
            ),
        ]
        self.expect_result = Response(data=self.stadiums)

    @patch('app.persistence.database.stadium.browse', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock):
        mock_browse.return_value = self.stadiums

        result = await stadium.search_stadium(params=self.params)

        self.assertEqual(result, self.expect_result)
        mock_browse.assert_called_with(
            name=self.params.name,
            city_id=self.params.city_id,
            district_id=self.params.district_id,
            sport_id=self.params.sport_id,
        )
