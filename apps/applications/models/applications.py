from django.db import models

from apps.core.models import BaseModel
from apps.recruitments.models import Recruitment
from apps.users.models.user import User


# 스터디 지원 내역
class Application(BaseModel):
    class ApplicationStatus(models.TextChoices):
        PENDING = "PENDING", "대기중"
        CANCELED = "CANCELED", "취소됨"
        ACCEPTED = "ACCEPTED", "승인됨"
        REJECTED = "REJECTED", "거절됨"

    # Recruitment.applications 으로 사용 가능
    recruitment_id = models.ForeignKey(
        Recruitment,
        on_delete=models.SET_NULL,
        null=True,  # , or IntegrityError
        related_name="applications",
        help_text="지원한 공고의 ID",
    )

    # User.applications
    user_id = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        related_name="applications",
        help_text="지원한 사용자 ID",
    )
    objective = models.CharField(max_length=300, null=False, help_text="목표")
    motivation = models.TextField(null=False, help_text="지원동기")
    self_introduction = models.TextField(null=False, help_text="자기소개")
    available_time = models.CharField(max_length=255, null=False, help_text="가능한 시간대와 요일")
    has_study_experience = models.BooleanField(default=False, null=False, help_text="과거 스터디 경험 여부")
    study_experience = models.TextField(null=True, blank=True, help_text="스터디 경험")
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING,
        null=False,
        help_text="공고 지원 상태",
    )

    class Meta:
        db_table = "applications"
        # unique_together = (('recruitment_id', 'user_id'),)  # DEPRECATED
        constraints = [models.UniqueConstraint(fields=["recruitment_id", "user_id"], name="UQ_recruitments_users_IDX")]

    def __str__(self) -> str:
        return f"{self.user_id.nickname}'s application for {self.recruitment_id.title}"
