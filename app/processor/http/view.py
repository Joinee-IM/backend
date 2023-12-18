from typing import Sequence

from fastapi import APIRouter, Depends, Query, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.persistence.database as db
from app.base import enums, vo
from app.middleware.headers import get_auth_token
from app.utils import Limit, Offset, Response, context

router = APIRouter(
    tags=['View'],
    default_response_class=responses.JSONResponse,
)


class ViewMyReservationParams(BaseModel):
    account_id: int
    is_manager: bool | None = None
    time_ranges: Sequence[vo.DateTimeRange] | None = None
    has_vacancy: bool | None = None
    member_status: enums.ReservationMemberStatus | None = None
    reservation_status: enums.ReservationStatus | None = None
    source: enums.ReservationMemberSource | None = None
    sort_by: enums.ViewMyReservationSortBy = enums.ViewMyReservationSortBy.time
    order: enums.Sorter = enums.Sorter.desc
    limit: int = Limit
    offset: int = Offset


class ViewMyReservationOutput(BaseModel):
    data: Sequence[vo.ViewMyReservation]
    total_count: int
    limit: int
    offset: int


@router.post('/view/my-reservation')
async def view_my_reservation(data: ViewMyReservationParams, _=Depends(get_auth_token))\
        -> Response[ViewMyReservationOutput]:
    if context.account.id != data.account_id:
        raise exc.NoPermission

    reservations, total_count = await db.view.browse_my_reservation(
        account_id=data.account_id,
        request_time=context.request_time,
        is_manager=data.is_manager,
        time_ranges=data.time_ranges,
        has_vacancy=data.has_vacancy,
        member_status=data.member_status,
        reservation_status=data.reservation_status,
        source=data.source,
        sort_by=data.sort_by,
        order=data.order,
        limit=data.limit,
        offset=data.offset,
    )
    return Response(
        data=ViewMyReservationOutput(
            data=reservations,
            total_count=total_count,
            limit=data.limit,
            offset=data.offset,
        ),
    )


class ViewProviderStadiumParams(BaseModel):
    city_id: int | None = Query(default=None)
    district_id: int | None = Query(default=None)
    is_published: bool | None = Query(default=None)
    sort_by: enums.ViewProviderStadiumSortBy = Query(default=enums.ViewProviderStadiumSortBy.district_name)
    order: enums.Sorter = Query(default=enums.Sorter.asc)
    limit: int | None = Query(default=None)
    offset: int | None = Query(default=None)


class ViewProviderStadiumOutput(BaseModel):
    data: Sequence[vo.ViewProviderStadium]
    total_count: int
    limit: int | None
    offset: int | None


@router.get('/view/stadium/provider')
async def view_provider_stadium(
    params: ViewProviderStadiumParams = Depends(),
    _=Depends(get_auth_token),
) -> Response[ViewProviderStadiumOutput]:
    account = await db.account.read(account_id=context.account.id)

    if account.role != enums.RoleType.provider:
        raise exc.NoPermission

    stadiums, total_count = await db.view.browse_provider_stadium(
        owner_id=account.id,
        city_id=params.city_id,
        district_id=params.district_id,
        is_published=params.is_published,
        sort_by=params.sort_by,
        order=params.order,
        limit=params.limit,
        offset=params.offset,
    )

    return Response(
        data=ViewProviderStadiumOutput(
            data=stadiums,
            total_count=total_count,
            limit=params.limit,
            offset=params.offset,
        ),
    )


class ViewProviderVenueParams(BaseModel):
    stadium_id: int | None = Query(default=None)
    is_published: bool | None = Query(default=None)
    sort_by: enums.ViewProviderVenueSortBy = Query(default=enums.ViewProviderVenueSortBy.stadium_name)
    order: enums.Sorter = Query(default=enums.Sorter.asc)
    limit: int | None = Query(default=None)
    offset: int | None = Query(default=None)


class ViewProviderVenueOutput(BaseModel):
    data: Sequence[vo.ViewProviderVenue]
    total_count: int
    limit: int | None
    offset: int | None


@router.get('/view/venue/provider')
async def view_provider_venue(
    params: ViewProviderVenueParams = Depends(),
    _=Depends(get_auth_token),
) -> Response[ViewProviderVenueOutput]:
    account = await db.account.read(account_id=context.account.id)

    if account.role != enums.RoleType.provider:
        raise exc.NoPermission

    venues, total_count = await db.view.browse_provider_venue(
        owner_id=account.id,
        stadium_id=params.stadium_id,
        is_published=params.is_published,
        sort_by=params.sort_by,
        order=params.order,
        limit=params.limit,
        offset=params.offset,
    )

    return Response(
        data=ViewProviderVenueOutput(
            data=venues,
            total_count=total_count,
            limit=params.limit,
            offset=params.offset,
        ),
    )


class ViewProviderCourtParams(BaseModel):
    stadium_id: int | None = Query(default=None)
    venue_id: int | None = Query(default=None)
    is_published: bool | None = Query(default=None)
    sort_by: enums.ViewProviderCourtSortBy = Query(default=enums.ViewProviderCourtSortBy.stadium_name)
    order: enums.Sorter = Query(default=enums.Sorter.asc)
    limit: int | None = Query(default=None)
    offset: int | None = Query(default=None)


class ViewProviderCourtOutput(BaseModel):
    data: Sequence[vo.ViewProviderCourt]
    total_count: int
    limit: int | None
    offset: int | None


@router.get('/view/court/provider')
async def view_provider_court(
    params: ViewProviderCourtParams = Depends(),
    _=Depends(get_auth_token),
) -> Response[ViewProviderCourtOutput]:
    account = await db.account.read(account_id=context.account.id)

    if account.role != enums.RoleType.provider:
        raise exc.NoPermission

    court, total_count = await db.view.browse_provider_court(
        owner_id=account.id,
        stadium_id=params.stadium_id,
        is_published=params.is_published,
        sort_by=params.sort_by,
        order=params.order,
        limit=params.limit,
        offset=params.offset,
    )

    return Response(
        data=ViewProviderCourtOutput(
            data=court,
            total_count=total_count,
            limit=params.limit,
            offset=params.offset,
        ),
    )
