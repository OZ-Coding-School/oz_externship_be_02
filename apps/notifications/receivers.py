from typing import Any, Optional

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.applications.models import Application
from apps.notifications.services.noti_create_service import (
    ApplicationNotificationService,
)


@receiver(
    pre_save, sender=Application, dispatch_uid="application_track_prev_status"
)  # 이전 status / pre_save = 저장되기 전
def prev_status(instance: Application, **kwargs: Any) -> None:
    if not instance.pk:  # 새로 만드는 객체라면 이전 상태 없음
        prev: Optional[str] = None
    else:  # 이미 DB에 있던 객체라면 저장되어 있던 이전 status를 읽어와 prev에 넣음
        prev = Application.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
    setattr(instance, "status_was", prev)


@receiver(post_save, sender=Application, dispatch_uid="notify_add_application")
def notify_add_application(instance: Application, created: bool, **kwargs: Any) -> None:
    if not created:
        return

    app_id = instance.pk

    def add_application() -> None:
        ApplicationNotificationService.from_id(app_id).notify_add_application()

    transaction.on_commit(add_application)


@receiver(post_save, sender=Application, dispatch_uid="notify_status_change_to_applicant")
def notify_status_change_to_applicant(instance: Application, created: bool, **kwargs: Any) -> None:
    if created:  # 신규 생성이 아닌 업데이트 하는거기에
        return

    app_id = instance.pk
    prev: Optional[str] = getattr(instance, "status_was", None)  # pre_save 때 붙여둔 임시 속성을 꺼내옴
    curr = instance.status  # 현재 상태

    if prev == curr:  # 이전과 현재가 같을 경우 X
        return

    if curr == Application.ApplicationStatus.ACCEPTED:  # 현재가 승인  상태로 바뀐 경우만

        def accept_application() -> None:
            ApplicationNotificationService.from_id(app_id).notify_application_accept()

        def join_study_group() -> None:
            ApplicationNotificationService.from_id(app_id).notify_group_members_join()

        transaction.on_commit(accept_application)
        transaction.on_commit(join_study_group)

    if curr == Application.ApplicationStatus.REJECTED:

        def reject_application() -> None:
            ApplicationNotificationService.from_id(app_id).notify_application_reject()

        transaction.on_commit(reject_application)
