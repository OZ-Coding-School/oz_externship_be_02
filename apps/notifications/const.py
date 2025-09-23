from typing import Any, Dict

from apps.notifications.models import Notification

# 알림 타입별 기본 URL 패턴
BACK_URL_LINK_BY_NOTIFICATION_TYPE: Dict[Notification.NotificationType, str] = {
    Notification.NotificationType.STUDY_REVIEW_REQUEST: "/my-page/completed-study",
    Notification.NotificationType.STUDY_JOIN: "/study-group/{group_id}/chat",
    Notification.NotificationType.STUDY_NOTE_CREATE: "/study-group/{group_id}",
    Notification.NotificationType.APPLICATION_ACCEPT: "/my-page/applications",
    Notification.NotificationType.APPLICATION_REJECT: "/my-page/applications",
    Notification.NotificationType.ADD_APPLICATION: "/my-page/applications",
    Notification.NotificationType.TODAY_SCHEDULE: "/study-group/{group_id}",
    Notification.NotificationType.UPCOMING_SCHEDULE: "/study-group/{group_id}",
}


def get_notification_back_url(notification_type: Notification.NotificationType, **kwargs: Any) -> str:
    url = BACK_URL_LINK_BY_NOTIFICATION_TYPE.get(notification_type)
    if not url:
        return "/my-page"

    try:
        return url.format(**kwargs)
    except KeyError:
        return url
