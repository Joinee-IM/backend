from typing import Sequence

from fastapi import APIRouter, responses
from pydantic import BaseModel

import app.persistence.database as db
from app.base import do, enums
from app.utils import Response

router = APIRouter(
    tags=['Album'],
    default_response_class=responses.JSONResponse,
)


class BrowseAlbumInput(BaseModel):
    place_id: int
    place_type: enums.PlaceType


@router.get('/album')
async def browse_album(params: BrowseAlbumInput) -> Response[Sequence[do.Album]]:
    albums = await db.album.browse(
        place_type=params.place_type,
        place_id=params.place_id,
    )
    return Response(data=albums)
