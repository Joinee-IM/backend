from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, Request, responses
from pydantic import BaseModel
from starlette.responses import RedirectResponse

import app.exceptions as exc
import app.persistence.database as db
from app.base import enums
from app.client.oauth import oauth_handler
from app.config import service_config
from app.middleware.headers import get_auth_token
from app.persistence.file_storage.gcs import gcs_handler
from app.utils import Response
from app.utils.security import encode_jwt

router = APIRouter(
    tags=['Google'],
    default_response_class=responses.JSONResponse,
)


@router.get('/google-login')
async def google_login(request: Request, role: enums.RoleType | None = None):
    return await oauth_handler.login(request=request, state=role)


@router.get('/auth_callback')
async def auth(request: Request):
    search_str = 'access_denied'
    if search_str.encode('utf-8') in request['query_string']:
        response = RedirectResponse(url=f"{service_config.url}/login")
        return response
    else:
        token_google = await oauth_handler.authorize_access_token(request=request)
        user_email = token_google['userinfo']['email']
        try:
            account_id, _, role, _ = await db.account.read_by_email(email=user_email)
            await db.account.update_google_token(
                account_id=account_id,
                access_token=token_google['access_token'],
                refresh_token=token_google['refresh_token'],
            )
        except exc.NotFound:
            role = enums.RoleType(request.query_params.get('state'))
            account_id = await db.account.add(
                email=user_email, is_google_login=True,
                nickname=user_email.split("@")[0],
                role=role,
                access_token=token_google['access_token'],
                refresh_token=token_google['refresh_token'],
            )
        token = encode_jwt(account_id=account_id, role=role)
        response = RedirectResponse(url=f"{service_config.url}", status_code=303)
        response.set_cookie(key="account_id", value=str(account_id), samesite='none', secure=True, httponly=True)
        response.set_cookie(key="token", value=str(token), samesite='none', secure=True, httponly=True)
        return response


@router.get('/file/download')
async def read_file(file_uuid: UUID, _=Depends(get_auth_token)) -> Response[str]:
    file = await db.gcs_file.read(file_uuid=file_uuid)
    url = await gcs_handler.sign_url(filename=file.filename)
    return Response(data=url)


class BatchDownloadInput(BaseModel):
    file_uuids: Sequence[UUID]


class BatchDownloadOutput(BaseModel):
    file_uuid: UUID
    sign_url: str


@router.get('/file/download/batch')
async def batch_download_files(data: BatchDownloadInput, _=Depends(get_auth_token)) \
        -> Response[Sequence[BatchDownloadOutput]]:
    return Response(
        data=[
            BatchDownloadOutput(
                file_uuid=file_uuid,
                sign_url=await gcs_handler.sign_url(filename=str(file_uuid)),
            )
            for file_uuid in data.file_uuids
        ],
    )
