from typing import TYPE_CHECKING

from django.contrib.auth.base_user import BaseUserManager
from django.db import models

if TYPE_CHECKING:
    from apps.users.models.user import User


class UserManager(models.Manager["User"]):
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

