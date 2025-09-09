from typing import TYPE_CHECKING

from django.db import models
from django.db.models import QuerySet

if TYPE_CHECKING:
    from .models import Notification


class NotificationManager(models.Manager["Notification"]):
    def list_queryset(self, user_id: int, status: str) -> QuerySet["Notification"]:
        qs = (
            self.get_queryset()
            .filter(user_id=user_id)
            .only("id", "content", "notification_type", "is_read", "back_url_link", "created_at")
        )

        if status == "unread":
            qs = qs.filter(is_read=False)
        elif status == "read":
            qs = qs.filter(is_read=True)

        return qs
