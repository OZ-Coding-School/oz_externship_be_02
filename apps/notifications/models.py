# oz_externship_be/apps/notifications/models.py
from django.db import models
from apps.core.models.base import BaseModel

class Notification(BaseModel):
    class NotificationType(models.TextChoices):
        STUDY_JOIN = "STUDY_JOIN", "스터디 참여"
        STUDY_NOTE_CREATE = "STUDY_NOTE_CREATE", "스터디 기록 작성"
        STUDY_REVIEW_REQUEST = "STUDY_REVIEW_REQUEST", "스터디 후기 요청"
        APPLICATION_ACCEPT = "APPLICATION_ACCEPT", "지원 수락"
        APPLICATION_REJECT = "APPLICATION_REJECT", "지원 거절"
        ADD_APPLICATION = "ADD_APPLICATION", "신규 지원"
        TODAY_SCHEDULE = "TODAY_SCHEDULE", "오늘의 스케줄"
        UPCOMMING_SCHEDULE = "UPCOMMING_SCHEDULE", "임박한 스케줄"

    user = models.ForeignKey(
        "users.User",
        # 사용자가 삭제 -> 해당 사용자의 알림도 함께 삭제
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    content = models.CharField(max_length=300)
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices
    )
    is_read = models.BooleanField(default=False)
    back_url_link = models.CharField(max_length=2048) # URL은 길어질 수 있으므로

    def __str__(self):
        return f"Notification for {self.user.nickname}: {self.content[:30]}"

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

