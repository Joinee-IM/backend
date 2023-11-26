from typing import Sequence

from fastapi import APIRouter, responses
from pydantic import BaseModel

import app.persistence.database as db
from app.base import vo
from app.utils import Limit, Offset, Response

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
    return Response(data=BrowseStadiumOutput(data=stadiums, total_count=row_count))


@router.get('/stadium/{stadium_id}')
async def read_stadium(stadium_id: int) -> Response[vo.ViewStadium]:
    stadium = await db.stadium.read(stadium_id=stadium_id)
    return Response(data=stadium)
