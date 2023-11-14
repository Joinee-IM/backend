from typing import Sequence

from fastapi import APIRouter, responses

import app.persistence.database as db
from app.base import do
from app.utils import Response

router = APIRouter(
    tags=['Sport'],
    default_response_class=responses.JSONResponse,
)


@router.get('/sport')
async def browse_sport() -> Response[Sequence[do.Sport]]:
    sports = await db.sport.browse()
    return Response(data=sports)
