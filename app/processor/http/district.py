from typing import Sequence

from fastapi import APIRouter, responses

import app.persistence.database as db
from app.base import do
from app.utils import Response

router = APIRouter(
    tags=['District'],
    default_response_class=responses.JSONResponse,
)


@router.get('/district')
async def browse_district(city_id: int) -> Response[Sequence[do.District]]:
    districts = await db.district.browse(city_id=city_id)
    return Response(data=districts)
