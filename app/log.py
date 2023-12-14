import logging

import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler

from app.config import app_config


class LoggingHandlerInherited(CloudLoggingHandler):
    def __init__(self, **kwargs):
        super().__init__(client=google.cloud.logging.Client(), **kwargs)


logger = logging.getLogger(app_config.logger_name)
