from fastapi import Request
import log


async def middleware(request: Request, call_next):
    log.info(msg='', extra={'request': {'method': request.method,
                                        'path': request.url.path,
                                        'params': request.query_params}})
    response = await call_next(request)
    return response
