from typing import TYPE_CHECKING, Any

from django.contrib.auth.base_user import BaseUserManager
from django.db import models

if TYPE_CHECKING:
    from apps.users.models.user import User


class UserManager(BaseUserManager["User"]):
    # 탈퇴하지않은 유저 조회
    def active(self) -> models.QuerySet["User"]:
        return self.filter(is_active=True)

    # 관리자 권한 있는 유저 조회
    def staff_users(self) -> models.QuerySet["User"]:
        return self.filter(is_staff=True)

    def create_user(self, email: str, password: str, **extra_fields: Any) -> "User":
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(email=self.normalize_email(email), **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields: Any) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password=password, **extra_fields)

    def exists_email(self, email: str) -> bool:
        """
        이메일 중복 확인
        """
        return self.active().filter(email=email).exists()

    def exists_nickname(self, nickname: str) -> bool:
        """
        닉네임 중복 확인
        """
        return self.active().filter(nickname=nickname).exists()

    def exists_phone(self, phone_number: str) -> bool:
        return self.active().filter(phone_number=phone_number).exists()
