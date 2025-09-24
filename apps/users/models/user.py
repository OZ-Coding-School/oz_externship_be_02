from django.contrib.auth.models import AbstractBaseUser
from django.db import models

from apps.core.models.base import UUIDBaseModel
from apps.users.managers.user_manager import UserManager


class User(UUIDBaseModel, AbstractBaseUser):
    email = models.EmailField(
        help_text="email address",
        max_length=255,
        unique=True,
    )
    name = models.CharField(max_length=30, null=True, blank=True, help_text="이름")
    nickname = models.CharField(max_length=10, help_text="닉네임")
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True, help_text="휴대폰 번호")
    gender = models.CharField(max_length=6, null=True, blank=True, help_text="성별")
    birthday = models.DateField(null=True, blank=True, help_text="생일")
    profile_img_url = models.URLField(max_length=255, null=True, blank=True, help_text="프로필 이미지")

    is_active = models.BooleanField(default=False, help_text="계정활성화 여부")
    is_staff = models.BooleanField(default=False, help_text="스태프 여부")
    is_superuser = models.BooleanField(default=False, help_text="슈퍼 유저 여부")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nickname", "name", "phone_number", "gender", "birthday"]

    objects = UserManager()

    def __str__(self) -> str:
        return self.email
