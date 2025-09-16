import logging

from django.conf import settings

if not settings.DEBUG:
    logger = logging.getLogger("django")
else:
    logger = logging.getLogger("django.server")
