import logging
import traceback

from starlette_context import context


logger = logging.getLogger(__name__)


def info(msg, extra=None):
    logger.info(f"request {context['request_uuid']}\t{msg}", extra=extra)


def debug(msg, extra=None):
    logger.debug(f"request {context['request_uuid']}\t{msg}", extra=extra)


def error(msg, extra=None):
    logger.error(f"request {context['request_uuid']}\t{msg}", extra=extra)


def exception(exc: Exception, msg='', info_level=False):
    if info_level:
        logger.info(f"{format_exc(exc)}\n{traceback.format_exc()}")
    else:
        logger.error(f"request {context['request_uuid']}\t{msg}\t{exc.__repr__()}")
        logger.exception(exc)


def format_exc(e: Exception):
    return f"{type(e).__name__}: {e}"