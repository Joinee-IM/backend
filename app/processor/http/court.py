from datetime import date, datetime, timedelta
from typing import Sequence

from fastapi import APIRouter, Depends, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.persistence.database as db
import app.persistence.email as email
from app.base import do, enums, vo
from app.client import google_calendar
from app.middleware.headers import get_auth_token
from app.utils import Response, ServerTZDatetime, context, invitation_code

router = APIRouter(
    tags=['Court'],
    default_response_class=responses.JSONResponse,
)


class BatchEditCourtInput(BaseModel):
    court_ids: Sequence[int]
    is_published: bool | None


@router.patch('/court/batch')
async def batch_edit_court(data: BatchEditCourtInput, _=Depends(get_auth_token)) -> Response:
    courts = await db.court.batch_read(court_ids=data.court_ids, include_unpublished=True)
    venues = await db.venue.batch_read(
        venue_ids=list(set(court.venue_id for court in courts)),
        include_unpublished=True,
    )
    stadiums = await db.stadium.batch_read(
        stadium_ids=list(set(venue.stadium_id for venue in venues)),
        include_unpublished=True,
    )
    if not all(context.account.id == stadium.owner_id for stadium in stadiums):
        raise exc.NoPermission

    await db.court.batch_edit(
        court_ids=data.court_ids,
        is_published=data.is_published,
    )

    return Response()


class BrowseReservationParameters(BaseModel):
    time_ranges: Sequence[vo.DateTimeRange] | None = None
    start_date: date | None = None


class BrowseReservationOutput(BaseModel):
    start_date: date
    reservations: Sequence[do.Reservation]


@router.post('/court/{court_id}/reservation/browse')
async def browse_reservation_by_court_id(court_id: int, params: BrowseReservationParameters) \
        -> Response[BrowseReservationOutput]:
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

    reservations, _ = await db.reservation.browse(
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

    reservations, _ = await db.reservation.browse(
        court_id=court_id,
        start_date=available_date,
    )
    return Response(
        data=BrowseReservationOutput(
            reservations=reservations,
            start_date=available_date,
        ),
    )


class AddReservationInput(BaseModel):
    start_time: ServerTZDatetime
    end_time: ServerTZDatetime
    technical_level: Sequence[enums.TechnicalType] = []
    remark: str | None
    member_count: int
    vacancy: int = -1
    member_ids: Sequence[int] = []


class AddReservationOutput(BaseModel):
    id: int


@router.post('/court/{court_id}/reservation')
async def add_reservation(court_id: int, data: AddReservationInput, _=Depends(get_auth_token)) \
        -> Response[AddReservationOutput]:
    account_id = context.account.id

    court = await db.court.read(court_id=court_id)
    venue = await db.venue.read(venue_id=court.venue_id)

    if not venue.is_reservable:
        raise exc.VenueUnreservable

    if data.start_time > context.request_time + timedelta(days=venue.reservation_interval):
        raise exc.CourtUnreservable

    reservations, _ = await db.reservation.browse(
        court_id=court_id,
        time_ranges=[
            vo.DateTimeRange(
                start_time=data.start_time,
                end_time=data.end_time,
            ),
        ],
    )

    if reservations:
        raise exc.CourtReserved

    if data.start_time < context.request_time or data.start_time >= data.end_time:
        raise exc.IllegalInput

    invite_code = invitation_code.generate()

    reservation_id = await db.reservation.add(
        court_id=court_id,
        venue_id=venue.id,
        stadium_id=venue.stadium_id,
        start_time=data.start_time,
        end_time=data.end_time,
        technical_level=data.technical_level,
        invitation_code=invite_code,
        remark=data.remark,
        member_count=data.member_count,
        vacancy=data.vacancy,
    )
    members = [
        do.ReservationMember(
            reservation_id=reservation_id,
            account_id=member_id,
            is_manager=member_id == account_id,
            status=enums.ReservationMemberStatus.joined if member_id == account_id else enums.ReservationMemberStatus.invited,  # noqa
            source=enums.ReservationMemberSource.invitation_code,
        ) for member_id in list(data.member_ids) + [account_id]
    ]
    await db.reservation_member.batch_add_with_do(members=members)

    account = await db.account.read(account_id=account_id)
    stadium = await db.stadium.read(stadium_id=venue.stadium_id)
    location = f'{stadium.name} {venue.name} 第 {court.number} {venue.court_type}'
    if data.member_ids:
        invitees = await db.account.batch_read(account_ids=data.member_ids)
        await email.invitation.send(
            meet_code=invite_code,
            bcc=', '.join(invitee.email for invitee in invitees),
        )
    if account.is_google_login:
        await google_calendar.add_google_calendar_event(
            reservation_id=reservation_id,
            start_time=data.start_time,
            end_time=data.end_time,
            account_id=account_id,
            location=location,
        )
    return Response(data=AddReservationOutput(id=reservation_id))


class EditCourtInput(BaseModel):
    is_published: bool | None = None


@router.patch('/court/{court_id}')
async def edit_court(court_id: int, data: EditCourtInput, _=Depends(get_auth_token)) -> Response:
    court = await db.court.read(court_id=court_id, include_unpublished=True)
    venue = await db.venue.read(venue_id=court.venue_id, include_unpublished=True)
    stadium = await db.stadium.read(stadium_id=venue.stadium_id, include_unpublished=True)

    if stadium.owner_id != context.account.id:
        raise exc.NoPermission

    await db.court.edit(
        court_id=court_id,
        is_published=data.is_published,
    )
    return Response()


class AddCourtInput(BaseModel):
    venue_id: int
    add: int


@router.post('/court')
async def batch_add_court(data: AddCourtInput, _=Depends(get_auth_token)) -> Response[bool]:
    venue = await db.venue.read(venue_id=data.venue_id)
    stadium = await db.stadium.read(stadium_id=venue.stadium_id)

    if stadium.owner_id != context.account.id or context.account.role != enums.RoleType.provider:
        raise exc.NoPermission

    await db.court.batch_add(venue_id=data.venue_id, add=data.add, start_from=venue.court_count + 1)

    return Response(data=True)
