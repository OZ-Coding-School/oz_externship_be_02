from typing import Dict

from celery import shared_task
from django.utils import timezone

from apps.notifications.services.noti_create_service import (
    StudyReviewNotificationService,
)


@shared_task(name="apps.notifications.tasks.study_review_requests_for_groups")
def study_review_requests_for_groups() -> Dict[str, int]:
    today = timezone.localdate()
    groups = StudyReviewNotificationService.get_groups_end(today)

    stats = {"groups_processed": 0, "notifications_created": 0}
    for g in groups.iterator(chunk_size=200):  # 메모리 절약용
        created = StudyReviewNotificationService.send_review_requests_for_groups(group=g, today=today)
        stats["groups_processed"] += 1
        stats["notifications_created"] += created

    return stats
