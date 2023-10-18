from fastapi import Request
from fastapi.responses import JSONResponse

import exceptions as exc
import log


async def middleware(request: Request, call_next):
    try:
        data = await call_next(request)
    except exc.NotFound as e:
        log.exception(e)
        data = JSONResponse(status_code=404, content={'error': e.__class__.__name__})
    except exc.IllegalInput as e:
        log.exception(e)
        data = JSONResponse(status_code=422, content={'error': e.__class__.__name__})
    except exc.NoPermission as e:
        log.exception(e)
        data = JSONResponse(status_code=401, content={'error': e.__class__.__name__})
    except Exception as e:
        log.exception(e)
        data = JSONResponse(status_code=500, content={'error': e.__class__.__name__})
    return data
