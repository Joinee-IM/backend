import app.exceptions as exc
import app.log as log
from fastapi import Request
from fastapi.responses import JSONResponse


async def middleware(request: Request, call_next):
    try:
        data = await call_next(request)
    except Exception as e:
        if isinstance(e, exc.AckException):
            data = JSONResponse(status_code=e.status_code,
                                content={'data': None, 'error': e.__class__.__name__})
        else:
            log.exception(e)
            data = JSONResponse(status_code=500, content={'data': None, 'error': e.__class__.__name__})
    return data
