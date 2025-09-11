from django.db import models

from apps.applications.managers.application_managers import ApplicationManager
from apps.core.models import BaseModel
from apps.recruitments.models.recruitments import Recruitment
from apps.users.models.user import User


# 스터디 지원 내역
class Application(BaseModel):
    class ApplicationStatus(models.TextChoices):
        PENDING = "PENDING", "대기중"
        CANCELED = "CANCELED", "취소됨"
        ACCEPTED = "ACCEPTED", "승인됨"
        REJECTED = "REJECTED", "거절됨"

    # Recruitment.applications 으로 사용 가능
    recruitment = models.ForeignKey(
        Recruitment,
        on_delete=models.SET_NULL,
        null=True,  # , or IntegrityError
        related_name="applications",
        help_text="지원한 공고의 ID",
    )

    # User.applications
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        related_name="applications",
        help_text="지원한 사용자 ID",
    )
    objective = models.CharField(max_length=300, help_text="목표")
    motivation = models.CharField(max_length=500, help_text="지원동기")
    self_introduction = models.CharField(max_length=500, help_text="자기소개")
    available_time = models.CharField(max_length=255, help_text="가능한 시간대와 요일")
    has_study_experience = models.BooleanField(default=False, help_text="과거 스터디 경험 여부")
    study_experience = models.CharField(max_length=1000, null=True, blank=True, help_text="스터디 경험")
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING,
        help_text="공고 지원 상태",
    )

    # 커스텀 매니저인 ApplicationManager를 기본 매니저('objects')로 지정합니다.
    # 이를 통해 Application.objects.create_application()과 같은 커스텀 메서드를 사용할 수 있게 됩니다.
    objects = ApplicationManager()

    class Meta:
        db_table = "applications"
        # unique_together = (('recruitment', 'user'),)  # DEPRECATED
        constraints = [models.UniqueConstraint(fields=["recruitment", "user"], name="UQ_recruitments_users_IDX")]

    def __str__(self) -> str:
        return f"{self.user.nickname}'s application for {self.recruitment.title if self.recruitment else 'None'}"
