from typing import Sequence

from fastapi import APIRouter, Depends, Query, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.persistence.database as db
from app import log
from app.base import do, enums, vo
from app.middleware.headers import get_auth_token
from app.utils import Limit, Offset, Response, context

router = APIRouter(
    tags=['Venue'],
    default_response_class=responses.JSONResponse,
)


class VenueSearchParameters(BaseModel):
    name: str | None = Query(default=None)
    stadium_id: int | None = Query(default=None)
    sport_id: int | None = Query(default=None)
    is_reservable: bool | None = Query(default=None)
    sort_by: enums.VenueAvailableSortBy = Query(default=enums.VenueAvailableSortBy.current_user_count)
    order: enums.Sorter = Query(default=enums.Sorter.desc)
    limit: int | None = Limit
    offset: int | None = Offset


class BrowseVenueOutput(BaseModel):
    data: Sequence[do.Venue]
    total_count: int
    limit: int | None = None
    offset: int | None = None


@router.get('/venue')
async def browse_venue(params: VenueSearchParameters = Depends()) -> Response[BrowseVenueOutput]:
    venues, total_count = await db.venue.browse(
        name=params.name,
        sport_id=params.sport_id,
        stadium_id=params.stadium_id,
        is_reservable=params.is_reservable,
        sort_by=params.sort_by,
        order=params.order,
        limit=params.limit,
        offset=params.offset,
    )
    return Response(
        data=BrowseVenueOutput(
            data=venues, total_count=total_count,
            limit=params.limit, offset=params.offset,
        ),
    )


class BatchEditVenueInput(BaseModel):
    venue_ids: Sequence[int]
    is_published: bool


@router.patch('/venue/batch')
async def batch_edit_venue(data: BatchEditVenueInput, _=Depends(get_auth_token)) -> Response:
    venues = await db.venue.batch_read(venue_ids=data.venue_ids, include_unpublished=True)
    stadiums = await db.stadium.batch_read(
        stadium_ids=list(set(venue.stadium_id for venue in venues)),
        include_unpublished=True,
    )
    if not all(context.account.id == stadium.owner_id for stadium in stadiums):
        raise exc.NoPermission
    await db.venue.batch_edit(venue_ids=data.venue_ids, is_published=data.is_published)
    return Response()


class ReadVenueOutput(do.Venue):
    sport_name: str


@router.get('/venue/{venue_id}')
async def read_venue(venue_id: int, _=Depends(get_auth_token)) -> Response[ReadVenueOutput]:
    venue = await db.venue.read(venue_id=venue_id, include_unpublished=True)
    sport = await db.sport.read(sport_id=venue.sport_id)
    return Response(
        data=ReadVenueOutput(
            **venue.model_dump(),
            sport_name=sport.name,
        ),
    )


class BrowseCourtByVenueIdParams(BaseModel):
    time_ranges: Sequence[vo.DateTimeRange] | None = None


# use post since get can't have body
@router.post('/venue/{venue_id}/court')
async def browse_court_by_venue_id(venue_id: int, params: BrowseCourtByVenueIdParams, _=Depends(get_auth_token))\
        -> Response[Sequence[do.Court]]:
    include_unpublished = context.account.role == enums.RoleType.provider if context.get_account() else False
    courts = await db.court.browse(
        venue_id=venue_id,
        include_unpublished=include_unpublished,
    )

    # return all if time ranges are not specified
    if not params.time_ranges:
        return Response(data=courts)

    available_courts = []
    for court in courts:
        reservations, _ = await db.reservation.browse(
            court_id=court.id,
            time_ranges=params.time_ranges,
        )
        log.logger.error(reservations)
        available_date = None

        for time_range in params.time_ranges:
            is_available = True
            for reservation in reservations:
                log.logger.error(time_range)
                log.logger.error((reservation.start_time, reservation.end_time))
                if reservation.start_time <= time_range.start_time \
                        and reservation.end_time >= time_range.end_time \
                        and reservation.vacancy <= 0:
                    is_available = False
            if is_available:
                available_date = time_range.start_time.date()
                break
        if not available_date:
            continue
        available_courts.append(court)

    return Response(data=available_courts)


class EditVenueInput(BaseModel):
    name: str | None = None
    floor: str | None = None
    area: int | None = None
    capacity: int | None = None
    sport_id: int | None = None
    is_reservable: bool | None = None
    reservation_interval: int | None = None
    is_chargeable: bool | None = None
    fee_rate: float | None = None
    fee_type: enums.FeeType | None = None
    sport_equipments: str | None = None
    facilities: str | None = None
    court_type: str | None = None


@router.patch('/venue/{venue_id}')
async def edit_venue(venue_id: int, data: EditVenueInput, _=Depends(get_auth_token)) -> Response:
    venue = await db.venue.read(venue_id=venue_id, include_unpublished=True)
    stadium = await db.stadium.read(stadium_id=venue.stadium_id, include_unpublished=True)

    if stadium.owner_id != context.account.id:
        raise exc.NoPermission

    await db.venue.edit(
        venue_id=venue.id,
        **data.model_dump(),
    )
    return Response()


class AddVenueInput(BaseModel):
    stadium_id: int
    name: str
    floor: str
    reservation_interval: int | None
    is_reservable: bool
    is_chargeable: bool
    fee_rate: float | None
    fee_type: enums.FeeType | None
    area: int
    capacity: int
    sport_equipments: str | None
    facilities: str | None
    court_count: int
    court_type: str
    sport_id: int
    business_hours: Sequence[vo.WeekTimeRange]


class AddVenueOutput(BaseModel):
    id: int


@router.post('/venue')
async def add_venue(data: AddVenueInput, _=Depends(get_auth_token)) -> Response[AddVenueOutput]:
    stadium = await db.stadium.read(stadium_id=data.stadium_id)

    if stadium.owner_id != context.account.id or context.account.role != enums.RoleType.provider:
        raise exc.NoPermission

    id_ = await db.venue.add(
        stadium_id=data.stadium_id,
        name=data.name,
        floor=data.floor,
        reservation_interval=data.reservation_interval,
        is_reservable=data.is_reservable,
        is_chargeable=data.is_chargeable,
        fee_rate=data.fee_rate,
        fee_type=data.fee_type,
        area=data.area,
        capacity=data.capacity,
        sport_equipments=data.sport_equipments,
        facilities=data.facilities,
        court_count=data.court_count,
        court_type=data.court_type,
        sport_id=data.sport_id,
    )

    await db.business_hour.batch_add(
        place_type=enums.PlaceType.venue,
        place_id=id_,
        business_hours=data.business_hours,
    )

    await db.court.batch_add(
        venue_id=id_,
        add=data.court_count,
        start_from=1,
    )

    return Response(data=AddVenueOutput(id=id_))
