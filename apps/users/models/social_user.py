from django.db import models

from .user import User
from ...core.models import BaseModel


class SocialUser(BaseModel):
    class ProviderChoices(models.TextChoices):
        KAKAO = "KAKAO", "카카오"
        NAVER = "NAVER", "네이버"
    user = models.ForeignKey("users.user", on_delete=models.CASCADE, help_text="유저")
    provider = models.CharField(max_length=10, choices=ProviderChoices.choices, help_text="소셜 로그인 제공 업체")
    provider_id = models.CharField(max_length=255, null=False, help_text="소셜 로그인 업체 고유 ID")


    def __str__(self) -> str:
        return f"{self.provider} - {self.user.email}"
