from typing import Any

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
)
from django.db import models

from apps.core.models.base import UUIDBaseModel


class UserManager(BaseUserManager["User"]):
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


class User(UUIDBaseModel, AbstractBaseUser):
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    name = models.CharField(max_length=30, null=False, blank=False, verbose_name="이름")
    nickname = models.CharField(max_length=10, unique=True, null=False, blank=False, verbose_name="닉네임")
    phone_number = models.CharField(max_length=20, unique=True, null=False, blank=False, verbose_name="휴대폰 번호")
    gender = models.CharField(max_length=6, null=False, blank=False, verbose_name="성별")
    birthday = models.DateField(null=False, blank=False, verbose_name="생일")
    profile_img_url = models.URLField(
        max_length=255, null=True, blank=True, verbose_name="프로필 이미지", help_text="유저 프로필 이미지"
    )

    is_active = models.BooleanField(default=False, verbose_name="계정활성화 여부")
    is_staff = models.BooleanField(default=False, verbose_name="스태프 여부")
    is_superuser = models.BooleanField(default=False, verbose_name="슈퍼 유저 여부")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname", "name", "phone_number", "gender", "birthday"]

    objects = UserManager()

    def __str__(self) -> str:
        return self.email
