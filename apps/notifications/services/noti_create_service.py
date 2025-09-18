from django.db import transaction

from apps.applications.models.applications import Application
from apps.notifications.models import Notification
from apps.studies.models import GroupMember


class ApplicationNotificationService:
    def __init__(self, app: Application):
        self.app = app

    @classmethod
    def from_instance(cls, app: Application) -> "ApplicationNotificationService":
        return cls(app)

    @classmethod
    def from_id(cls, app_id: int) -> "ApplicationNotificationService":
        app = Application.objects.select_related("recruitment__author", "recruitment__study_group", "user").get(
            pk=app_id
        )
        return cls(app)

    def notification_add_application(self) -> Notification:
        rec = self.app.recruitment
        if rec is None:  # mypy
            raise ValueError("Application.recruitment is None")

        return Notification.objects.create(
            user_id=rec.author_id,
            content=f"{rec.title} 구인 공고에 신규 지원자가 있습니다.",
            notification_type=Notification.NotificationType.ADD_APPLICATION,
            back_url_link=f"/recruitments/{rec.uuid}/applications",
        )

    def notification_application_accept(self) -> Notification:
        if self.app.status != Application.ApplicationStatus.ACCEPTED:
            raise ValueError("Application status is not accepted")

        rec = self.app.recruitment
        if rec is None:
            raise ValueError("Recruitment is None")

        return Notification.objects.create(
            user_id=self.app.user_id,
            content=f"{rec.title} 구인 공고에 대한 지원 내역이 승인 되었습니다.",
            notification_type=Notification.NotificationType.APPLICATION_ACCEPT,
            back_url_link=f"/my-page/applications",
        )

    def notification_application_reject(self) -> Notification:
        if self.app.status != Application.ApplicationStatus.REJECTED:
            raise ValueError("Application.status is not REJECTED")

        rec = self.app.recruitment
        if rec is None:
            raise ValueError("Application.recruitment is None")

        return Notification.objects.create(
            user_id=self.app.user_id,  # 수신자 = 지원자
            content=f"{rec.title} 구인 공고에 대한 지원 내역이 거절되었습니다.",
            notification_type=Notification.NotificationType.APPLICATION_REJECT,
            back_url_link="/my-page/applications",
        )

    def notification_group_members_join(self) -> int:
        if self.app.status != Application.ApplicationStatus.ACCEPTED:
            return 0
        rec = self.app.recruitment
        if rec is None:  # mypy
            return 0
        group = rec.study_group

        new_user = self.app.user

        # 그룹에 참여중인 멤버들
        accepted_user_ids = set(GroupMember.objects.filter(study_group=group.id).values_list("user_id", flat=True))

        accepted_user_ids.discard(new_user.id)
        if not accepted_user_ids:
            return 0

        notifications = [
            Notification(
                user_id=uid,
                content=f"{group.name}에 {new_user.nickname} 님이 참여했습니다. 환영해주세요!",
                notification_type=Notification.NotificationType.STUDY_JOIN,
                back_url_link=f"/study-groups/{group.id}/chat",
            )
            for uid in accepted_user_ids
        ]

        with transaction.atomic():
            created = Notification.objects.bulk_create(notifications)

        return len(created)
