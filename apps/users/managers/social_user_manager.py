from django.contrib.auth.base_user import BaseUserManager
from django.db import models

class SocialUserManager(models.Manager):
    def kakao_users(self):
        return self.filter(provider='kakao')
    def naver_users(self):
        return self.filter(provider='naver')