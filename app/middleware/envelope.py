from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

import app.exceptions as exc
import app.log as log


async def middleware(request: Request, call_next):
    try:
        data = await call_next(request)
    except Exception as e:
        if isinstance(e, exc.AckException):
            data = JSONResponse(
                status_code=e.status_code,
                content={'data': None, 'error': e.__class__.__name__},
            )
        elif isinstance(e, ValidationError):
            log.info(e)
            data = JSONResponse(
                status_code=422,
                content={'data': None, 'error': 'IllegalInput'},
            )
        else:
            log.exception(e)
            data = JSONResponse(status_code=500, content={'data': None, 'error': e.__class__.__name__})
    return data
