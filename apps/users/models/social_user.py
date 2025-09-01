from django.db import models

from .user import User


class SocialUser(models.Model):
    class ProviderChoices(models.TextChoices):
        KAKAO = "KAKAO", "카카오"
        NAVER = "NAVER", "네이버"

    id = models.BigAutoField(primary_key=True, editable=False)
    user = models.ForeignKey("users.user", on_delete=models.CASCADE, verbose_name="유저")
    provider = models.CharField(max_length=10, choices=ProviderChoices.choices, verbose_name="소셜 로그인 제공 업체")
    provider_id = models.CharField(max_length=255,null=False,  verbose_name="소셜 로그인 업체 고유 ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생설 일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정 일시")

    def __str__(self):
        return f"{self.provider} - {self.user.email}"