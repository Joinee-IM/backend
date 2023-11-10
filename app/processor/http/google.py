from fastapi import APIRouter, Depends, Request, responses
from starlette.responses import RedirectResponse

import app.exceptions as exc
import app.persistence.database as db
from app.client.oauth import oauth_handler
from app.config import service_config
from app.middleware.headers import get_auth_token
from app.utils.security import encode_jwt

router = APIRouter(
    tags=['Google'],
    default_response_class=responses.JSONResponse,
    dependencies=[Depends(get_auth_token)]
)


@router.get('/google-login')
async def google_login(request: Request):
    return await oauth_handler.login(request=request)


@router.get('/auth')
async def auth(request: Request):
    search_str = 'access_denied'
    if search_str.encode('utf-8') in request['query_string']:
        response = RedirectResponse(url=f"{service_config.url}/login")
        return response
    else:
        token_google = await oauth_handler.authorize_access_token(request=request)
        user_email = token_google['userinfo']['email']
        try:
            account_id, *_ = await db.account.read_by_email(email=user_email)
            await db.account.update_google_token(account_id=account_id,
                                                 access_token=token_google['access_token'],
                                                 refresh_token=token_google['refresh_token'])
        except exc.NotFound:
            account_id = await db.account.add(email=user_email, is_google_login=True,
                                              access_token=token_google['access_token'],
                                              refresh_token=token_google['refresh_token'])
        token = encode_jwt(account_id=account_id)
        response = RedirectResponse(url=f"{service_config.url}/login")
        response.set_cookie(key="account_id", value=str(account_id))
        response.set_cookie(key="token", value=str(token))
        return response