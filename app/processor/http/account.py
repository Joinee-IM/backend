from fastapi import APIRouter, Depends, UploadFile, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.log as log
import app.persistence.database as db
import app.persistence.file_storage as fs
from app.base import do, enums
from app.middleware.headers import get_auth_token
from app.utils import Response, context

router = APIRouter(
    tags=['Account'],
    default_response_class=responses.JSONResponse,
    dependencies=[Depends(get_auth_token)],
)


@router.get('/account/{account_id}')
async def read_account(account_id: int) -> Response[do.Account]:
    if account_id != context.account.id:
        raise exc.NoPermission

    account = await db.account.read(account_id=account_id)
    return Response(data=account)


class EditAccountInput(BaseModel):
    nickname: str | None = None
    gender: enums.GenderType | None = None


@router.patch('/account/{account_id}')
async def edit_account(account_id: int, data: EditAccountInput) -> Response[bool]:
    if account_id != context.account.id:
        raise exc.NoPermission

    await db.account.edit(
        account_id=account_id,
        nickname=data.nickname,
        gender=data.gender,
    )
    return Response(data=True)


@router.patch('/account/{account_id}/upload')
async def upload_account_image(account_id: int, image: UploadFile) -> Response[bool]:
    if context.account.id != account_id:
        raise exc.NoPermission

    if image.content_type not in ['image/jpeg']:
        log.info(f'received content_type {image.content_type}, denied.')
        raise exc.IllegalInput

    file_uuid, bucket = await fs.avatar.upload(image.file)
    await db.gcs_file.add(file_uuid=file_uuid, key=str(file_uuid), bucket=bucket, filename=str(file_uuid))
    await db.account.edit(account_id=account_id, image_uuid=file_uuid)

    return Response(data=True)
