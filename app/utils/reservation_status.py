from datetime import datetime

from app.base import enums
from app.utils import context


def compose_reservation_status(end_time: datetime, is_cancelled: bool) -> enums.ReservationStatus:
    if is_cancelled:
        return enums.ReservationStatus.cancelled
    if context.request_time > end_time:
        return enums.ReservationStatus.finished
    return enums.ReservationStatus.in_progress
