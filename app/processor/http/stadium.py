from typing import Sequence

from fastapi import APIRouter, Depends, Query, responses
from pydantic import BaseModel

import app.persistence.database as db
from app.base import vo
from app.utils import Limit, Offset, Response

router = APIRouter(
    tags=['Stadium'],
    default_response_class=responses.JSONResponse,
)


class StadiumSearchParameters(BaseModel):
    name: str | None = Query(default=None)
    city_id: int | None = Query(default=None)
    district_id: int | None = Query(default=None)
    sport_id: int | None = Query(default=None)
    limit: int = Limit
    offset: int = Offset


@router.get('/stadium')
async def browse_stadium(params: StadiumSearchParameters = Depends()) -> Response[Sequence[vo.ViewStadium]]:
    stadiums = await db.stadium.browse(
        name=params.name,
        city_id=params.city_id,
        district_id=params.district_id,
        sport_id=params.sport_id,
    )
    return Response(data=stadiums)
