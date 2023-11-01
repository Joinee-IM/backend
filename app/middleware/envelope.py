from fastapi import Request
from fastapi.responses import JSONResponse

import app.exceptions as exc
import app.log as log

EXCEPTION_MAP = {
    exc.NoPermission: 401,
    exc.LoginExpired: 401,
    exc.LoginFailed: 401,
    exc.NotFound: 404,
    exc.IllegalInput: 422,
}


async def middleware(request: Request, call_next):
    try:
        data = await call_next(request)
    except tuple(EXCEPTION_MAP.keys()) as e:
        data = JSONResponse(status_code=EXCEPTION_MAP[e.__class__],
                            content={'data': None, 'error': e.__class__.__name__})
    except Exception as e:
        log.exception(e)
        data = JSONResponse(status_code=500, content={'data': None, 'error': e.__class__.__name__})
    return data
