from datetime import datetime
from typing import Sequence

from fastapi import APIRouter, Depends, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.persistence.database as db
from app.base import do, enums, vo
from app.client import google_calendar
from app.middleware.headers import get_auth_token
from app.utils import Limit, Offset, Response, context

router = APIRouter(
    tags=['Reservation'],
    default_response_class=responses.JSONResponse,
)


class BrowseReservationParameters(BaseModel):
    city_id: int | None = None
    district_id: int | None = None
    sport_id: int | None = None
    stadium_id: int | None = None
    time_ranges: Sequence[vo.DateTimeRange] | None = None
    technical_level: enums.TechnicalType | None = None
    limit: int = Limit
    offset: int = Offset
    sort_by: enums.BrowseReservationSortBy = enums.BrowseReservationSortBy.time
    order: enums.Sorter = enums.Sorter.desc


class BrowseReservationOutput(BaseModel):
    data: Sequence[do.Reservation]
    total_count: int
    limit: int
    offset: int


# use POST here since GET can't process request body
@router.post('/view/reservation')
async def browse_reservation(params: BrowseReservationParameters) -> Response[BrowseReservationOutput]:
    reservations, total_count = await db.reservation.browse(
        city_id=params.city_id,
        district_id=params.district_id,
        sport_id=params.sport_id,
        stadium_id=params.stadium_id,
        time_ranges=params.time_ranges,
        technical_level=params.technical_level,
        limit=params.limit,
        offset=params.offset,
        sort_by=params.sort_by,
        order=params.order,
    )

    return Response(
        data=BrowseReservationOutput(
            data=reservations,
            total_count=total_count,
            limit=params.limit,
            offset=params.offset,
        ),
    )


@router.get('/reservation/{reservation_id}')
async def read_reservation(reservation_id: int) -> Response[do.Reservation]:
    reservation = await db.reservation.read(reservation_id=reservation_id)
    return Response(data=reservation)


@router.post('/reservation/code/{invitation_code}')
async def join_reservation(invitation_code: str, _=Depends(get_auth_token)) -> Response[bool]:
    account_id = context.account.id
    reservation = await db.reservation.read_by_code(invitation_code=invitation_code)

    if reservation.vacancy <= 0:
        raise exc.ReservationFull

    await db.reservation_member.batch_add(
        reservation_id=reservation.id,
        member_ids=[account_id],
    )

    await google_calendar.add_google_calendar_event_member(
        reservation_id=reservation.id,
        member_id=account_id,
    )

    return Response(data=True)


@router.delete('/reservation/{reservation_id}')
async def delete_reservation(reservation_id: int, _=Depends(get_auth_token)) -> Response:
    reservation_member = await db.reservation_member.browse(
        reservation_id=reservation_id,
        account_id=context.account.id,
    )

    if not reservation_member or not reservation_member[0].is_manager:
        raise exc.NoPermission

    await db.reservation.delete(reservation_id=reservation_id)
    return Response()


class EditReservationInput(BaseModel):
    court_id: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    vacancy: int | None = None
    technical_levels: Sequence[enums.TechnicalType] | None = None
    remark: str | None = None


@router.patch('/reservation/{reservation_id}')
async def edit_reservation(reservation_id: int, data: EditReservationInput, _=Depends(get_auth_token)) -> Response:
    reservation_member = await db.reservation_member.browse(
        reservation_id=reservation_id,
        account_id=context.account.id,
    )

    if not reservation_member or not reservation_member[0].is_manager:
        raise exc.NoPermission

    reservation = await db.reservation.read(reservation_id=reservation_id)

    court = await db.court.read(court_id=data.court_id or reservation.court_id)
    venue = await db.venue.read(venue_id=court.venue_id)
    start_time = data.start_time or reservation.start_time
    end_time = data.end_time or reservation.end_time

    if start_time < context.request_time or start_time >= end_time:
        raise exc.IllegalInput

    reservations, _ = await db.reservation.browse(
        court_id=court.id,
        time_ranges=[
            vo.DateTimeRange(
                start_time=start_time,
                end_time=end_time,
            ),
        ],
    )

    if len(reservations) >= 1 and reservation not in reservations:
        raise exc.CourtReserved

    await db.reservation.edit(
        reservation_id=reservation_id,
        court_id=court.id,
        venue_id=venue.id,
        stadium_id=venue.stadium_id,
        start_time=start_time,
        end_time=end_time,
        vacancy=data.vacancy,
        technical_levels=data.technical_levels,
        remark=data.remark,
    )

    stadium = await db.stadium.read(stadium_id=venue.stadium_id)
    location = f"{stadium.name} {venue.name} 第 {court.number} {venue.court_type}"
    await google_calendar.update_google_event(
        reservation_id=reservation_id,
        location=location,
        start_time=start_time,
        end_time=end_time,
    )

    return Response()


@router.delete('/reservation/{reservation_id}/leave')
async def leave_reservation(reservation_id: int, _=Depends(get_auth_token)) -> Response:
    reservation_member = await db.reservation_member.browse(
        reservation_id=reservation_id,
        account_id=context.account.id,
    )
    if not reservation_member:
        raise exc.NotFound

    reservation_members = await db.reservation_member.browse(reservation_id=reservation_id)
    if len(reservation_members) > 1:
        await db.reservation_member.leave(
            reservation_id=reservation_id,
            account_id=context.account.id,
        )
    else:
        await db.reservation.delete(reservation_id=reservation_id)

    return Response()
