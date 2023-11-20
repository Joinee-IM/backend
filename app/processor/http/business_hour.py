from typing import Sequence

from fastapi import APIRouter, Depends, Query, responses
from pydantic import BaseModel

import app.persistence.database as db
from app.base import do, enums
from app.utils import Response

router = APIRouter(
    tags=['Business Hour'],
    default_response_class=responses.JSONResponse,
)


class BrowseBusinessHourParams(BaseModel):
    place_type: enums.PlaceType = Query()
    place_id: int = Query()


@router.get('/business-hour')
async def browse_business_hour(params: BrowseBusinessHourParams = Depends()) -> Response[Sequence[do.BusinessHour]]:
    business_hour = await db.business_hour.browse(
        place_type=params.place_type,
        place_id=params.place_id,
    )
    return Response(data=business_hour)
