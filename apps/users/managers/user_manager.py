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
