from typing import Sequence

from fastapi import APIRouter, Depends, Query, responses
from pydantic import BaseModel

import app.persistence.database as db
from app.base import enums
from app.persistence.file_storage.gcs import gcs_handler
from app.utils import Response

router = APIRouter(
    tags=['Album'],
    default_response_class=responses.JSONResponse,
)


class BrowseAlbumInput(BaseModel):
    place_id: int = Query()
    place_type: enums.PlaceType = Query()


class BrowseAlbumOutput(BaseModel):
    urls: Sequence[str]


@router.get('/album')
async def browse_album(params: BrowseAlbumInput = Depends()) -> Response[BrowseAlbumOutput]:
    albums = await db.album.browse(
        place_type=params.place_type,
        place_id=params.place_id,
    )

    return Response(
        data=BrowseAlbumOutput(
            urls=[
                await gcs_handler.sign_url(filename=str(album.file_uuid))
                for album in albums
            ]
        )
    )
