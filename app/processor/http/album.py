from io import BytesIO
from typing import Sequence

from fastapi import APIRouter, Depends, File, Query, UploadFile, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.log as log
import app.persistence.database as db
from app.base import do, enums
from app.const import ALLOWED_MEDIA_TYPE, BUCKET_NAME
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


@router.post('/album')
async def batch_add_album(place_type: enums.PlaceType, place_id: int,
                          files: Sequence[UploadFile] = File(...)):
    uuids = []
    for file in files:
        if file.content_type not in ALLOWED_MEDIA_TYPE:
            log.info(f'received content_type {file.content_type}, denied.')
            raise exc.IllegalInput
        uuids.append(await gcs_handler.upload(file=file.file, content_type=file.content_type, bucket_name=BUCKET_NAME,))

    await db.gcs_file.batch_add_with_do([
        do.GCSFile(
            uuid=uuid,
            key=str(uuid),
            bucket=BUCKET_NAME,
            filename=str(uuid),
        ) for uuid in uuids
    ])

    await db.album.batch_add(
        place_type=place_type,
        place_id=place_id,
        uuids=uuids,
    )

    return Response(
        data=BrowseAlbumOutput(
            urls=[
                await gcs_handler.sign_url(filename=str(uuid))
                for uuid in uuids
            ]
        )
    )
