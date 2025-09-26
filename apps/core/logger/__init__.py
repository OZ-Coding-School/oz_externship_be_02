import logging

from django.conf import settings


def get_logger() -> logging.Logger:
    if not settings.DEBUG:
        return logging.getLogger("django")
    return logging.getLogger("django.server")


logger = get_logger()
