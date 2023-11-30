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
    account_id: int = Query()
    sort_by: enums.ViewMyReservationSortBy = Query(default=enums.ViewMyReservationSortBy.time)
    order: enums.Sorter = Query(default=enums.Sorter.desc)
    limit: int = Limit
    offset: int = Offset


class ViewMyReservationOutput(BaseModel):
    data: Sequence[vo.ViewMyReservation]
    total_count: int
    limit: int
    offset: int


@router.get('/view/reservation')
async def view_my_reservation(params: ViewMyReservationParams = Depends(), _=Depends(get_auth_token))\
        -> Response[ViewMyReservationOutput]:
    if context.account.id != params.account_id:
        raise exc.NoPermission

    reservations, total_count = await db.view.browse_my_reservation(
        account_id=params.account_id,
        sort_by=params.sort_by,
        order=params.order,
        limit=params.limit,
        offset=params.offset,
    )
    return Response(data=ViewMyReservationOutput(
        data=reservations,
        total_count=total_count,
        limit=params.limit,
        offset=params.offset,
    ))


class ViewProviderStadiumParams(BaseModel):
    city_id: int | None = Query(default=None)
    district_id: int | None = Query(default=None)
    is_published: bool | None = Query(default=None)
    sort_by: enums.ViewProviderStadiumSortBy = Query(default=enums.ViewProviderStadiumSortBy.district_name)
    order: enums.Sorter = Query(default=enums.Sorter.asc)
    limit: int = Limit
    offset: int = Offset


class ViewProviderStadiumOutput(BaseModel):
    data: Sequence[vo.ViewProviderStadium]
    total_count: int
    limit: int
    offset: int


@router.get('/view/stadium/provider')
async def view_provider_stadium(params: ViewProviderStadiumParams = Depends(),
                                _=Depends(get_auth_token)) -> Response[ViewProviderStadiumOutput]:
    account = await db.account.read(account_id=context.account.id)

    if account.role is not enums.RoleType.provider:
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

    return Response(data=ViewProviderStadiumOutput(
        data=stadiums,
        total_count=total_count,
        limit=params.limit,
        offset=params.offset,
    ))
