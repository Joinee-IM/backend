from typing import Sequence

from fastapi import APIRouter, Depends, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.persistence.database as db
from app.base import vo
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
    limit: int = Limit
    offset: int = Offset


class BrowseStadiumOutput(BaseModel):
    data: Sequence[vo.ViewStadium]
    total_count: int
    limit: int
    offset: int


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


@router.get('/stadium/{stadium_id}')
async def read_stadium(stadium_id: int) -> Response[vo.ViewStadium]:
    stadium = await db.stadium.read(stadium_id=stadium_id)
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
