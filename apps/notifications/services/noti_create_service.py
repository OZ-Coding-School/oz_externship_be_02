from apps.applications.models.applications import Application
from apps.notifications.models import Notification


class NotificationCreateApplicationService:
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
