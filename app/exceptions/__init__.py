import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import app.const as const

from .ack_exception import (
    AckException,
    CourtReserved,
    CourtUnreservable,
    EmailExists,
    IllegalInput,
    LoginExpired,
    LoginFailed,
    NoPermission,
    NotFound,
    ReservationFull,
    UniqueViolationError,
    VenueUnreservable,
    WrongPassword,
)


def register_exception_handlers(app: FastAPI):
    import app.log as log

    @app.exception_handler(LoginFailed)
    @app.exception_handler(LoginExpired)
    def login_failed_exception_handler(_: Request, exc_: LoginFailed | LoginExpired):
        log.logger.info(f'Raised AckException {exc_.__class__.__name__}, cleaning cookie.')
        response = JSONResponse(
            status_code=exc_.status_code,
            content={'data': None, 'error': exc_.__class__.__name__},
        )
        response.delete_cookie(const.COOKIE_ACCOUNT_KEY)
        response.delete_cookie(const.COOKIE_TOKEN_KEY)
        return response

    @app.exception_handler(AckException)
    def exception_handler(_: Request, exc_: AckException):
        log.logger.info(f'Raised AckException {exc_.__class__.__name__}')
        return JSONResponse(
            status_code=exc_.status_code,
            content={'data': None, 'error': exc_.__class__.__name__},
        )

    @app.exception_handler(Exception)
    def general_exception_handler(_: Request, exc_: Exception):
        log.logger.error(exc_)
        traceback_str = traceback.format_exc()
        log.logger.error(f'Traceback:\n{traceback_str}')
        return JSONResponse(
            status_code=500,
            content={'data': None, 'error': exc_.__class__.__name__},
        )

    @app.exception_handler(RequestValidationError)
    def validation_exception_handler(_: Request, exc_: RequestValidationError):
        log.logger.info(exc_)
        return JSONResponse(
            status_code=422,
            content={'data': None, 'error': 'IllegalInput'},
        )
