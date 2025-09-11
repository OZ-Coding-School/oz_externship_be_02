from typing import TYPE_CHECKING

from django.db import models
from django.db.models import QuerySet

if TYPE_CHECKING:
    from .models import Notification


class NotificationManager(models.Manager["Notification"]):
    def get_list_by_user_id_and_is_read(self, user_id: int, is_read: bool) -> QuerySet["Notification"]:
        return self.get_queryset().filter(user_id=user_id, is_read=is_read)

    def unread_count(self, user_id: int) -> int:
        return self.get_queryset().filter(user_id=user_id, is_read=False).count()
