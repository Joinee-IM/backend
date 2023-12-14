from fastapi import Request

import app.log as log


async def middleware(request: Request, call_next):
    log.logger.info(
        msg=f'{request.method} {request.url.path}, params: {request.query_params},',
        extra={
            'request': {
                'method': request.method,
                'path': request.url.path,
                'params': request.query_params,
            },
        },
    )
    response = await call_next(request)
    return response
