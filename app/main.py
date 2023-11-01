with open('logging.yaml', 'r') as conf:
    import yaml
    log_config = yaml.safe_load(conf.read())
    import logging.config
    logging.config.dictConfig(log_config)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware


from app.config import app_config
from app import log

app = FastAPI(
    title=app_config.title,
    docs_url=app_config.docs_url,
    redoc_url=app_config.redoc_url,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.on_event('startup')
async def app_startup():
    log.info('app start.')
    # from app.config import pg_config
    # from app.persistence.database import pg_pool_handler
    # await pg_pool_handler.initialize(db_config=pg_config)

    # if redis needed
    # from app.config import redis_config
    # from app.persistence.redis import redis_pool_handler
    # await redis_pool_handler.initialize(db_config=redis_config)


@app.on_event('shutdown')
async def app_shutdown():
    log.info('app shutdown')
    # from app.persistence.database import pg_pool_handler
    # await pg_pool_handler.close()

    # if redis needed
    # from app.persistence.redis import redis_pool_handler
    # await redis_pool_handler.close()


from app.middleware import envelope
app.middleware('http')(envelope.middleware)

from app.middleware import logging
app.middleware('http')(logging.middleware)

from app.middleware import auth
app.middleware('http')(auth.middleware)

import starlette_context.middleware
app.add_middleware(starlette_context.middleware.RawContextMiddleware)

from app.processor import http
http.register_routers(app)
