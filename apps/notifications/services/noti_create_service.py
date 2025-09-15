from apps.applications.models.applications import Application
from apps.notifications.models import Notification


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
            back_url_link=f"/applications/me",
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
            back_url_link="/applications/me",
        )
