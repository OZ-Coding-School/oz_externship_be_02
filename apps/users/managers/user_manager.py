from django.contrib.auth.base_user import BaseUserManager
from django.db import models

class UserManager(models.Manager):
    # 탈퇴하지않은 유저 조회
    def active(self):
        return self.filter(is_active=True)
    # 관리자 권한 있는 유저 조회
    def staff_users(self):
        return self.filter(is_staff=True)

