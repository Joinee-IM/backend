from datetime import date, datetime
from typing import Sequence

from fastapi import APIRouter, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.persistence.database as db
from app.base import do, enums, vo
from app.utils import Response

router = APIRouter(
    tags=['Court'],
    default_response_class=responses.JSONResponse,
)


class BrowseReservationParameters(BaseModel):
    time_ranges: Sequence[vo.DateTimeRange] | None = None
    start_date: date | None = None


class BrowseReservationOutput(BaseModel):
    start_date: date
    reservations: Sequence[do.Reservation]


@router.post('/court/{court_id}/reservation/browse')
async def browse_reservation_by_court_id(court_id: int, params: BrowseReservationParameters) -> Response:
    """
    這隻 func 如果給了 start_date 會直接 return start_date ~ start_date + 7 的資料，
    要透過 time range 搜尋的話要給 start_date = null

    time format 要給 naive datetime, e.g. `2023-11-11T11:11:11`
    """
    court = await db.court.read(court_id=court_id)
    business_hours = await db.business_hour.browse(
        place_type=enums.PlaceType.venue,
        place_id=court.venue_id,
    )
    if not business_hours:
        raise exc.NotFound

    if not params.start_date and not params.time_ranges:
        params.start_date = datetime.now().date()

    reservations = await db.reservation.browse_by_court_id(
        court_id=court_id,
        time_ranges=params.time_ranges,
        start_date=params.start_date,
    )
    if params.start_date:
        return Response(
            data=BrowseReservationOutput(
                reservations=reservations,
                start_date=params.start_date,
            ),
        )

    available_date = None
    is_available = True

    for time_range in params.time_ranges:
        for reservation in reservations:
            if reservation.start_time <= time_range.start_time \
                    and reservation.end_time >= time_range.end_time\
                    and not reservation.vacancy:
                is_available = False
        if is_available:
            available_date = time_range.start_time.date()
            break

    if not available_date:
        raise exc.NotFound  # TODO: ask pm/designer not found's behavior

    reservations = await db.reservation.browse_by_court_id(
        court_id=court_id,
        start_date=available_date,
    )
    return Response(
        data=BrowseReservationOutput(
            reservations=reservations,
            start_date=available_date,
        ),
    )
