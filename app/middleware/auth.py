import datetime
import uuid

from fastapi import Request

from app.utils.context import context
from app.config import app_config


async def middleware(request: Request, call_next):
    request_uuid, request_time = uuid.uuid1(), datetime.datetime.now()
    context.set_request_time(request_time)
    context.set_request_uuid(request_uuid)
    response = await call_next(request)
    response.headers['X-Request-UUID'] = str(request_uuid)
    response.headers['Access-Control-Allow-Origin'] = ', '.join(app_config.allow_origins)
    return response
