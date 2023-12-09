import logging

import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler

from app.config import app_config
from app.utils.context import context


class LoggingHandlerInherited(CloudLoggingHandler):
    def __init__(self, **kwargs):
        super().__init__(client=google.cloud.logging.Client(), **kwargs)


logger = logging.getLogger(app_config.logger_name)


def info(msg, extra: dict = None):
    extra = {} if not extra else extra
    extra['request_uuid'] = context.get_request_uuid()
    logger.info(msg, extra=extra)


def error(msg, extra=None):
    extra = {} if not extra else extra
    extra['request_uuid'] = context.get_request_uuid()
    logger.error(msg, extra=extra)
