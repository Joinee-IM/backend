from typing import Sequence

from fastapi import APIRouter, Depends, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.persistence.database as db
from app.base import enums, vo
from app.client.google_maps import google_maps
from app.middleware.headers import get_auth_token
from app.utils import Limit, Offset, Response, context

router = APIRouter(
    tags=['Stadium'],
    default_response_class=responses.JSONResponse,
)


class StadiumSearchParameters(BaseModel):
    name: str | None = None
    city_id: int | None = None
    district_id: int | None = None
    sport_id: int | None = None
    time_ranges: Sequence[vo.WeekTimeRange] | None = None
    limit: int | None = Limit
    offset: int | None = Offset


class BrowseStadiumOutput(BaseModel):
    data: Sequence[vo.ViewStadium]
    total_count: int
    limit: int | None = None
    offset: int | None = None


# use POST here since GET can't process request body
@router.post('/stadium/browse')
async def browse_stadium(params: StadiumSearchParameters) -> Response[BrowseStadiumOutput]:
    stadiums, row_count = await db.stadium.browse(
        name=params.name,
        city_id=params.city_id,
        district_id=params.district_id,
        sport_id=params.sport_id,
        time_ranges=params.time_ranges,
        limit=params.limit,
        offset=params.offset,
    )
    return Response(
        data=BrowseStadiumOutput(
            data=stadiums, total_count=row_count,
            limit=params.limit, offset=params.offset,
        ),
    )


class BatchEditStadiumInput(BaseModel):
    stadium_ids: Sequence[int]
    is_published: bool | None = None


@router.patch('/stadium/batch')
async def batch_edit_stadium(data: BatchEditStadiumInput, _=Depends(get_auth_token)) -> Response:
    stadiums = await db.stadium.batch_read(stadium_ids=data.stadium_ids, include_unpublished=True)
    if not all(stadium.owner_id == context.account.id for stadium in stadiums):
        raise exc.NoPermission

    venues = await db.venue.batch_read(stadium_ids=[stadium.id for stadium in stadiums])
    courts = await db.court.browse(venue_ids=[venue.id for venue in venues])

    await db.stadium.batch_edit(
        stadium_ids=data.stadium_ids,
        is_published=data.is_published,
    )

    if data.is_published is False:
        await db.venue.batch_edit(venue_ids=[venue.id for venue in venues], is_published=False)
        await db.court.batch_edit(court_ids=[court.id for court in courts], is_published=False)

    return Response()


@router.get('/stadium/{stadium_id}')
async def read_stadium(stadium_id: int, _=Depends(get_auth_token)) -> Response[vo.ViewStadium]:
    include_unpublished = context.account.role == enums.RoleType.provider if context.get_account() else False
    stadium = await db.stadium.read(stadium_id=stadium_id, include_unpublished=include_unpublished)
    return Response(data=stadium)


class EditStadiumInput(BaseModel):
    name: str | None = None
    address: str | None = None
    contact_number: str | None = None
    time_ranges: Sequence[vo.WeekTimeRange] | None = None
    is_published: bool | None = None


@router.patch('/stadium/{stadium_id}')
async def edit_stadium(stadium_id: int, data: EditStadiumInput, _=Depends(get_auth_token)) -> Response:
    stadium = await db.stadium.read(stadium_id=stadium_id, include_unpublished=True)
    if stadium.owner_id != context.account.id:
        raise exc.NoPermission

    await db.stadium.edit(
        stadium_id=stadium_id,
        name=data.name,
        address=data.address,
        contact_number=data.contact_number,
        time_ranges=data.time_ranges,
        is_published=data.is_published,
    )

    return Response()


class AddStadiumInput(BaseModel):
    name: str
    address: str
    district_id: int
    business_hours: Sequence[vo.WeekTimeRange]
    contact_number: str | None = None
    description: str | None = None


class AddStadiumOutput(BaseModel):
    id: int


@router.post('/stadium')
async def add_stadium(data: AddStadiumInput, _=Depends(get_auth_token)) -> Response[AddStadiumOutput]:
    if context.account.role != enums.RoleType.provider:
        raise exc.NoPermission

    long, lat = google_maps.get_long_lat(address=data.address)

    id_ = await db.stadium.add(
        name=data.name,
        address=data.address,
        district_id=data.district_id,
        owner_id=context.account.id,
        contact_number=data.contact_number,
        description=data.description,
        long=long,
        lat=lat,
    )

    await db.business_hour.batch_add(
        place_type=enums.PlaceType.stadium,
        place_id=id_,
        business_hours=data.business_hours,
    )

    return Response(data=AddStadiumOutput(id=id_))


class ValidateAddressOutput(BaseModel):
    long: float
    lat: float


@router.post('/validate_address')
async def validate_address(address: str) -> Response[ValidateAddressOutput]:
    long, lat = google_maps.get_long_lat(address=address)
    return Response(data=ValidateAddressOutput(long=long, lat=lat))
