from datetime import time
from unittest.mock import patch

from app.base import do, enums
from app.processor.http import business_hour
from app.utils import Response
from tests import AsyncMock, AsyncTestCase


class TestBrowseBusinessHour(AsyncTestCase):
    def setUp(self) -> None:
        self.params = business_hour.BrowseBusinessHourParams(
            place_type=enums.PlaceType.stadium,
            place_id=1,
        )
        self.business_hour = [
            do.BusinessHour(
                id=1,
                place_id=1,
                type=enums.PlaceType.stadium,
                weekday=1,
                start_time=time(10, 27),
                end_time=time(17, 27),
            ),
        ]
        self.expect_result = Response(
            data=self.business_hour,
        )

    @patch('app.persistence.database.business_hour.browse', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock):
        mock_browse.return_value = self.business_hour

        result = await business_hour.browse_business_hour(
            params=self.params,
        )

        self.assertEqual(result, self.expect_result)
