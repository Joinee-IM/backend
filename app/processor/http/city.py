from typing import Sequence

from fastapi import APIRouter, responses

import app.persistence.database as db
from app.base import do
from app.utils import Response

router = APIRouter(
    tags=['City'],
    default_response_class=responses.JSONResponse,
)


@router.get('/city')
async def browse_city() -> Response[Sequence[do.City]]:
    cities = await db.city.browse()
    return Response(data=cities)
