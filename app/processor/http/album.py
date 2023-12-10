from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.log as log
import app.persistence.database as db
from app.base import do, enums
from app.const import ALLOWED_MEDIA_TYPE, BUCKET_NAME
from app.middleware.headers import get_auth_token
from app.persistence.file_storage.gcs import gcs_handler
from app.utils import Response, context

router = APIRouter(
    tags=['Album'],
    default_response_class=responses.JSONResponse,
)


class BrowseAlbumInput(BaseModel):
    place_id: int = Query()
    place_type: enums.PlaceType = Query()


class BrowseAlbumOutput(BaseModel):
    file_uuid: UUID
    url: str


@router.get('/album')
async def browse_album(params: BrowseAlbumInput = Depends()) -> Response[Sequence[BrowseAlbumOutput]]:
    albums = await db.album.browse(
        place_type=params.place_type,
        place_id=params.place_id,
    )

    return Response(
        data=[
            BrowseAlbumOutput(
                file_uuid=album.file_uuid,
                url=await gcs_handler.sign_url(filename=str(album.file_uuid)),
            )
            for album in albums
        ],
    )


@router.post('/album')
async def batch_add_album(
    place_type: enums.PlaceType, place_id: int,
    files: Sequence[UploadFile] = File(...),
    _=Depends(get_auth_token),
):
    stadium_id = (await db.venue.read(venue_id=place_id, include_unpublished=True)).stadium_id \
        if place_type is enums.PlaceType else place_id

    stadium = await db.stadium.read(stadium_id=stadium_id, include_unpublished=True)
    if stadium.owner_id != context.account.id:
        raise exc.NoPermission

    uuids = []
    for file in files:
        if file.content_type not in ALLOWED_MEDIA_TYPE:
            log.logger.info(f'received content_type {file.content_type}, denied.')
            raise exc.IllegalInput
        uuids.append(await gcs_handler.upload(file=file.file, content_type=file.content_type, bucket_name=BUCKET_NAME))

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
        data=[
            BrowseAlbumOutput(
                file_uuid=uuid,
                url=await gcs_handler.sign_url(filename=str(uuid)),
            )
            for uuid in uuids
        ],
    )


class BatchDeleteAlbumInput(BaseModel):
    place_type: enums.PlaceType
    place_id: int
    uuids: Sequence[UUID]


@router.delete('/album/batch')
async def batch_delete_album(data: BatchDeleteAlbumInput, _=Depends(get_auth_token)) -> Response:
    stadium_id = (await db.venue.read(venue_id=data.place_id, include_unpublished=True)).stadium_id \
        if data.place_type is enums.PlaceType else data.place_id

    stadium = await db.stadium.read(stadium_id=stadium_id, include_unpublished=True)
    if stadium.owner_id != context.account.id:
        raise exc.NoPermission

    await db.album.batch_delete(
        place_type=data.place_type,
        place_id=data.place_id,
        uuids=data.uuids,
    )

    return Response()
