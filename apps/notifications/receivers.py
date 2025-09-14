from typing import Any

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.applications.models import Application
from apps.notifications.services.noti_create_service import (
    NotificationCreateApplicationService,
)


@receiver(post_save, sender=Application, dispatch_uid="notify_add_application")
def notify_add_application(instance: Application, created: bool, **kwargs: Any) -> None:
    if not created:
        return

    app_id = instance.pk

    def add_application() -> None:
        NotificationCreateApplicationService.notification_add_application_by_id(app_id)

    transaction.on_commit(add_application)
