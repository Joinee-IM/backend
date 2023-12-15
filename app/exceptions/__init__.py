import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import app.const as const
import app.log as log

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


def login_failed_exception_handler(_: Request, exc_: LoginFailed | LoginExpired) -> JSONResponse:
    log.logger.info(f'Raised AckException {exc_.__class__.__name__}, cleaning cookie.')
    response = JSONResponse(
        status_code=exc_.status_code,
        content={'data': None, 'error': exc_.__class__.__name__},
    )
    response.delete_cookie(const.COOKIE_ACCOUNT_KEY)
    response.delete_cookie(const.COOKIE_TOKEN_KEY)
    response.delete_cookie(const.COOKIE_ROLE_KEY)
    return response


def ack_exception_handler(_: Request, exc_: AckException):
    log.logger.info(f'Raised AckException {exc_.__class__.__name__}')
    return JSONResponse(
        status_code=exc_.status_code,
        content={'data': None, 'error': exc_.__class__.__name__},
    )


def general_exception_handler(_: Request, exc_: Exception):
    log.logger.error(exc_)
    traceback_str = traceback.format_exc()
    log.logger.error(f'Traceback:\n{traceback_str}')
    return JSONResponse(
        status_code=500,
        content={'data': None, 'error': exc_.__class__.__name__},
    )


def validation_exception_handler(_: Request, exc_: RequestValidationError):
    log.logger.info(exc_)
    return JSONResponse(
        status_code=422,
        content={'data': None, 'error': 'IllegalInput'},
    )


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(LoginFailed, login_failed_exception_handler)
    app.add_exception_handler(LoginExpired, login_failed_exception_handler)
    app.add_exception_handler(AckException, ack_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
