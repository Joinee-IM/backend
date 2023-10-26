import datetime
import uuid

from fastapi import Request
from app.utils.context import context

import app.security as security


async def middleware(request: Request, call_next):
    request_uuid, request_time = uuid.uuid1(), datetime.datetime.now()
    account = None
    if auth_token := request.headers.get('auth-token', None):
        account = security.decode_jwt(auth_token, time=request_time)
    context.set_account(account)
    context.set_request_time(request_time)
    context.set_request_uuid(request_uuid)
    response = await call_next(request)
    response.headers['X-Request-UUID'] = str(request_uuid)
    return response
