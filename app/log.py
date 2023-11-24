import logging
import traceback

from app.config import app_config
from app.utils.context import context

logger = logging.getLogger(app_config.logger_name)


def info(msg, extra: dict = None):
    extra = {} if not extra else extra
    extra['request_uuid'] = context.get_request_uuid()
    logger.info(msg, extra=extra)


def debug(msg, extra=None):
    extra = {} if not extra else extra
    extra['request_uuid'] = context.get_request_uuid()
    logger.debug(msg, extra=extra)


def error(msg, extra=None):
    extra = {} if not extra else extra
    extra['request_uuid'] = context.get_request_uuid()
    logger.error(msg, extra=extra)


def exception(exc: Exception, msg='', info_level=False, extra: dict = None):
    extra = {} if not extra else extra
    extra['request_uuid'] = context.get_request_uuid()
    if info_level:
        logger.info(f'{format_exc(exc)}\n{traceback.format_exc()}', extra=extra)
    else:
        logger.error(f'{msg}\t{exc.__repr__()}', extra=extra)
        logger.exception(exc, extra=extra)


def format_exc(e: Exception):
    return f'{type(e).__name__}: {e}'
