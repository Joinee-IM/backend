from typing import Sequence
from uuid import uuid4

from fastapi import APIRouter, Depends, UploadFile, responses
from pydantic import BaseModel

import app.exceptions as exc
import app.log as log
import app.persistence.database as db
import app.persistence.file_storage as fs
from app.base import do, enums
from app.const import ALLOWED_MEDIA_TYPE
from app.middleware.headers import get_auth_token
from app.persistence.file_storage.gcs import gcs_handler
from app.utils import Response, context, security, update_cookie

router = APIRouter(
    tags=['Account'],
    default_response_class=responses.JSONResponse,
    dependencies=[Depends(get_auth_token)],
)


class ReadAccountOutput(do.Account):
    image_url: str | None


@router.get('/account/{account_id}')
async def read_account(account_id: int) -> Response[ReadAccountOutput]:
    if account_id != context.account.id:
        raise exc.NoPermission

    account = await db.account.read(account_id=account_id)
    image_url = await gcs_handler.sign_url(filename=str(account.image_uuid)) if account.image_uuid else None
    return Response(
        data=ReadAccountOutput(
            **account.model_dump(),
            image_url=image_url,
        ),
    )


class EditAccountInput(BaseModel):
    nickname: str | None = None
    gender: enums.GenderType | None = None
    role: enums.RoleType | None = None


@router.patch('/account/{account_id}')
async def edit_account(account_id: int, data: EditAccountInput, response: responses.Response) -> Response[bool]:
    if account_id != context.account.id:
        raise exc.NoPermission

    await db.account.edit(
        account_id=account_id,
        nickname=data.nickname,
        gender=data.gender,
        role=data.role,
    )
    token = security.encode_jwt(account_id=account_id, role=data.role)
    _ = update_cookie(response=response, account_id=account_id, token=token)
    return Response(data=True)


@router.patch('/account/{account_id}/upload')
async def upload_account_image(account_id: int, image: UploadFile) -> Response[bool]:
    if context.account.id != account_id:
        raise exc.NoPermission

    if image.content_type not in ALLOWED_MEDIA_TYPE:
        log.info(f'received content_type {image.content_type}, denied.')
        raise exc.IllegalInput

    file_uuid = uuid4()
    file_uuid, bucket = await fs.avatar.upload(image.file, file_uuid=file_uuid, content_type=image.content_type)
    await db.gcs_file.add(file_uuid=file_uuid, key=str(file_uuid), bucket=bucket, filename=str(file_uuid))
    await db.account.edit(account_id=account_id, image_uuid=file_uuid)

    return Response(data=True)


@router.get('/account/search')
async def search_account(query: str) -> Response[Sequence[do.Account]]:
    accounts = await db.account.search(query=query)
    return Response(data=accounts)


class EditPasswordInput(BaseModel):
    old_password: str
    new_password: str


@router.patch('/account/{account_id}/password')
async def edit_password(account_id: int, data: EditPasswordInput, _=Depends(get_auth_token)) -> Response:
    if context.account.id != account_id:
        raise exc.NoPermission

    account = await db.account.read(account_id=account_id)
    _, pass_hash, *_ = await db.account.read_by_email(account.email)

    if not security.verify_password(data.old_password, pass_hash):
        raise exc.WrongPassword

    await db.account.edit(
        account_id=account_id,
        pass_hash=security.hash_password(data.new_password),
    )
    return Response()
