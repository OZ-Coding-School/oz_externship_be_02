from django.db import models

from apps.core.models.base import BaseModel

from .user import User


class WithdrawalsReasonChoices(models.TextChoices):
    NO_LONGER_NEEDED = "NO_LONGER_NEEDED", "서비스 이용할 시간이 없음"
    LACK_OF_INTEREST = "LACK_OF_INTEREST", "관심이 사라짐"
    TOO_DIFFICULT = "TOO_DIFFICULT", "서비스를 이용하기가 너무 어려움"
    FOUND_BETTER_SERVICE = "FOUND_BETTER_SERVICE", "더 좋은 대안을 찾음"
    PRIVACY_CONCERNS = "PRIVACY_CONCERNS", "개인정보/보안/우려"
    POOR_SERVICE_QUALITY = "POOR_SERVICE_QUALITY", "서비스 품질 불만"
    TECHNICAL_ISSUES = "TECHNICAL_ISSUES", "기술적문제(버그 등)"
    LACK_OF_CONTENT = "LACK_OF_CONTENT", "원하는 콘텐츠나 기능의 부족"
    OTHER = "OTHER", "기타"


class Withdrwals(BaseModel):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, unique=True, verbose_name="유저")
    reason = models.CharField(
        max_length=30, choices=WithdrawalsReasonChoices.choices, null=False, blank=False, verbose_name="탈퇴 사유"
    )
    reason_detail = models.DateField(null=False, blank=False, verbose_name="구체적인 탈퇴 사유")
    due_date = models.DateField(null=False, blank=False, verbose_name="계정 삭제 예정일")

    def __str__(self) -> str:
        return f"{self.user.email} - {self.reason}"
