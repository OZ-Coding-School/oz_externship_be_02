from typing import TYPE_CHECKING
from django.contrib.auth.base_user import BaseUserManager
from django.db import models

if TYPE_CHECKING:
    from apps.users.models.social_user import SocialUser
class SocialUserManager(models.Manager["SocialUser"]):
    def kakao_users(self) -> models.QuerySet["SocialUser"]:
        return self.filter(provider="kakao")

    def naver_users(self) -> models.QuerySet["SocialUser"]:
        return self.filter(provider="naver")
