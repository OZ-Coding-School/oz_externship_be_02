from typing import Optional

from django.db import transaction
from django.db.models import QuerySet
from rest_framework.exceptions import NotFound

from apps.notifications.models import Notification


class NotificationService:
    # 서비스에서는 Repository(Model Manager or 쿼리셋) 호출하여 비즈니스 로직 구성
    @classmethod
    def get_notifications_list(
        cls, user_id: int, is_read: Optional[bool] = None, n_type: Optional[str] = None
    ) -> QuerySet[Notification]:
        if is_read is None:
            n_list = Notification.objects.filter(user_id=user_id)
        else:
            n_list = Notification.objects.get_list_by_user_id_and_is_read(user_id=user_id, is_read=is_read)
        if n_type is not None:
            n_list = n_list.filter(notification_type=n_type)

        return n_list

    @classmethod
    @transaction.atomic
    def read_notification(cls, notification_id: int, user_id: int) -> None:
        try:
            notification = Notification.objects.get(id=notification_id, user_id=user_id)
        except Notification.DoesNotExist:
            raise NotFound
        notification.is_read = True
        notification.save()  # 하나의 알림만 수정하기 때문

    @classmethod
    @transaction.atomic
    def read_all_user_notifications(cls, user_id: int) -> int:
        notifications = Notification.objects.get_list_by_user_id_and_is_read(user_id=user_id, is_read=False)
        return notifications.update(is_read=True)

    @classmethod
    def get_unread_count(cls, user_id: int) -> int:
        return Notification.objects.unread_count(user_id=user_id)
