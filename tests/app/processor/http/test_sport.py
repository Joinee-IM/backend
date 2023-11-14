from unittest.mock import patch

from app.base import do
from app.processor.http import sport
from app.utils import Response
from tests import AsyncMock, AsyncTestCase


class TestBrowseSport(AsyncTestCase):
    def setUp(self) -> None:
        self.sports = [
            do.Sport(
                id=1,
                name='桌球',
            ),
            do.Sport(
                id=2,
                name='羽球',
            ),
        ]
        self.expect_result = Response(data=self.sports)

    @patch('app.persistence.database.sport.browse', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock):
        mock_browse.return_value = self.sports

        result = await sport.browse_sport()

        self.assertEqual(result, self.expect_result)
        mock_browse.assert_called()
