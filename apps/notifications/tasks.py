from typing import Dict

from celery import shared_task

from apps.notifications.services.noti_create_service import (
    ScheduleTodayNotificationService,
    ScheduleUpComingNotificationService,
    StudyReviewNotificationService,
)


@shared_task(name="apps.notifications.tasks.study_review_requests_for_groups")
def study_review_requests_for_groups() -> Dict[str, int]:
    return StudyReviewNotificationService.create_review_request_notifications_for_due_group()


@shared_task(name="apps.notifications.tasks.notify_today_schedules")
def notify_today_schedules() -> Dict[str, int]:
    return ScheduleTodayNotificationService.notify_all_today_schedules()


@shared_task(name="apps.notifications.tasks.notify_upcoming_schedules")
def notify_upcoming_schedules() -> Dict[str, int]:
    return ScheduleUpComingNotificationService.notify_all_upcoming_schedules()
