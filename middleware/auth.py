import datetime
import uuid

from fastapi import Request
from starlette_context import context

import security


async def middleware(request: Request, call_next):
    request_uuid, request_time = uuid.uuid1(), datetime.datetime.now()
    account = None
    if auth_token := request.headers.get('auth-token', None):
        account = security.decode_jwt(auth_token, time=request_time)
    context['account'] = account
    context['time'] = request_time
    context['request_uuid'] = request_uuid
    response = await call_next(request)
    response.headers['X-Request-UUID'] = str(request_uuid)
    return response
