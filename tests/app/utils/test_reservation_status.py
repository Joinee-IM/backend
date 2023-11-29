from datetime import datetime

from freezegun import freeze_time

from app.base import enums
from app.utils import reservation_status
from tests import MockContext, TestCase, patch


class TestComposeReservationStatus(TestCase):
    def setUp(self) -> None:
        self.context = {
            'REQUEST_TIME': datetime(2023, 11, 20),
        }

    @freeze_time('2023-11-11')
    def test_cancelled(self):
        result = reservation_status.compose_reservation_status(
            end_time=datetime(2023, 11, 11),
            is_cancelled=True,
        )
        self.assertEqual(result, enums.ReservationStatus.cancelled)

    @patch('app.utils.reservation_status.context', new_callable=MockContext)
    def test_finished(self, mock_context: MockContext):
        mock_context._context = self.context

        result = reservation_status.compose_reservation_status(
            end_time=datetime(2023, 11, 11),
            is_cancelled=False,
        )

        self.assertEqual(result, enums.ReservationStatus.finished)
        mock_context.reset_context()

    @patch('app.utils.reservation_status.context', new_callable=MockContext)
    def test_in_progress(self, mock_context: MockContext):
        mock_context._context = self.context

        result = reservation_status.compose_reservation_status(
            end_time=datetime(2023, 11, 30),
            is_cancelled=False,
        )

        self.assertEqual(result, enums.ReservationStatus.in_progress)
        mock_context.reset_context()
