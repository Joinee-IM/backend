from datetime import datetime

import app.exceptions as exc
from app.base import enums, vo
from app.processor.http import view
from app.utils import Response
from app.utils.security import AuthedAccount
from tests import AsyncMock, AsyncTestCase, MockContext, patch


class TestViewMyReservation(AsyncTestCase):
    def setUp(self) -> None:
        self.params = view.ViewMyReservationParams(
            account_id=1,
            sort_by=enums.ViewMyReservationSortBy.time,
            order=enums.Sorter.desc,
            limit=1,
            offset=0,
        )
        self.context = {'AUTHED_ACCOUNT': AuthedAccount(id=1, time=datetime(2023, 11, 4))}
        self.wrong_context = {'AUTHED_ACCOUNT': AuthedAccount(id=2, time=datetime(2023, 11, 4))}

        self.reservations = [
            vo.ViewMyReservation(
                start_time=datetime(2023, 11, 11),
                end_time=datetime(2023, 11, 17),
                stadium_name='stadium_name',
                venue_name='venue_name',
                is_manager=True,
                vacancy=1,
                status=enums.ReservationStatus.finished,
            ),
        ]
        self.expect_result = Response(data=self.reservations)

    @patch('app.processor.http.view.context', new_callable=MockContext)
    @patch('app.persistence.database.view.browse_my_reservation', new_callable=AsyncMock)
    async def test_happy_path(self, mock_browse: AsyncMock, mock_context: MockContext):
        mock_context._context = self.context
        mock_browse.return_value = self.reservations

        result = await view.view_my_reservation(params=self.params)

        self.assertEqual(result, self.expect_result)
        mock_browse.assert_called_with(
            account_id=self.params.account_id,
            sort_by=self.params.sort_by,
            order=self.params.order,
            limit=self.params.limit,
            offset=self.params.offset,
        )

        mock_context.reset_context()

    @patch('app.processor.http.view.context', new_callable=MockContext)
    async def test_no_permission(self, mock_context: MockContext):
        mock_context._context = self.wrong_context

        with self.assertRaises(exc.NoPermission):
            await view.view_my_reservation(params=self.params)

        mock_context.reset_context()
