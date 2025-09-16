from django.db import transaction

from apps.applications.models.applications import Application
from apps.notifications.models import Notification
from apps.studies.models import StudyGroup


class NotificationCreateApplicationService:
    # 공고 지원 시 알림
    @classmethod
    def notification_add_application_by_id(cls, app_id: int) -> Notification:  # N+1 방지를 위함
        app = Application.objects.select_related("recruitment__author", "recruitment", "user").get(pk=app_id)
        return cls.notification_add_application(app)

    @classmethod
    def notification_add_application(cls, app: Application) -> Notification:
        rec = app.recruitment
        if rec is None:  # mypy
            raise ValueError("Application.recruitment is None")

        return Notification.objects.create(
            user_id=rec.author_id,
            content=f"{rec.title} 구인 공고에 신규 지원자가 있습니다.",
            notification_type=Notification.NotificationType.ADD_APPLICATION,
            back_url_link=f"/recruitments/{rec.uuid}/applications",
        )

    # 지원자에게 승인 알림
    @classmethod
    def notification_application_accept_by_id(cls, app_id: int) -> Notification:  # N+1 방지를 위함
        app = Application.objects.select_related("recruitment__author", "recruitment", "user").get(pk=app_id)
        return cls.notification_application_accept(app)

    @classmethod
    def notification_application_accept(cls, app: Application) -> Notification:
        if app.status != Application.ApplicationStatus.ACCEPTED:
            raise ValueError("Application status is not accepted")

        rec = app.recruitment
        if rec is None:
            raise ValueError("Recruitment is None")

        return Notification.objects.create(
            user_id=app.user_id,
            content=f"{rec.title} 구인 공고에 대한 지원 내역이 승인 되었습니다.",
            notification_type=Notification.NotificationType.APPLICATION_ACCEPT,
            back_url_link=f"/my-page/applications",
        )

    # 지원자에게 거절 알림
    @classmethod
    def notification_application_reject_by_id(cls, app_id: int) -> Notification:
        app = Application.objects.select_related("recruitment__author", "recruitment", "user").get(pk=app_id)
        return cls.notification_application_reject(app)

    @classmethod
    def notification_application_reject(cls, app: Application) -> Notification:
        if app.status != Application.ApplicationStatus.REJECTED:
            raise ValueError("Application.status is not REJECTED")

        rec = app.recruitment
        if rec is None:
            raise ValueError("Application.recruitment is None")

        return Notification.objects.create(
            user_id=app.user_id,  # 수신자 = 지원자
            content=f"{rec.title} 구인 공고에 대한 지원 내역이 거절되었습니다.",
            notification_type=Notification.NotificationType.APPLICATION_REJECT,
            back_url_link="/my-page/applications",
        )

    @classmethod
    def notification_group_members_join_by_id(cls, app_id: int) -> int:
        app = Application.objects.select_related("recruitment__author", "recruitment__study_group", "user").get(
            pk=app_id
        )
        return cls.notification_group_members_join(app)

    @classmethod
    def notification_group_members_join(cls, app: Application) -> int:
        if app.status != Application.ApplicationStatus.ACCEPTED:
            return 0
        rec = app.recruitment
        if rec is None:  # mypy
            return 0
        group = rec.study_group
        if group is None:  # mypy
            return 0
        new_user = app.user

        # 그룹에 참여중인 멤버들
        accepted_user_ids = set(
            Application.objects.filter(
                recruitment__study_group=group.id, status=Application.ApplicationStatus.ACCEPTED
            ).values_list("user_id", flat=True)
        )

        if new_user.id in accepted_user_ids:
            accepted_user_ids.remove(new_user.id)

        notifications = [
            Notification(
                user_id=uid,
                content=f"{group.name}에 {new_user.nickname} 님이 참여했습니다. 환영해주세요!",
                notification_type=Notification.NotificationType.STUDY_JOIN,
                back_url_link=f"{group.id}",
            )
            for uid in accepted_user_ids
        ]

        with transaction.atomic():
            created = Notification.objects.bulk_create(notifications)

        return len(created)
