from django.db import models
from django.utils import timezone

class WithdrawalUserManager(models.Manager):
    # 2주 내에 탈퇴한 유저
    def recently_withdrawn(self):
        two_weeks_ago = timezone.now() - timezone.timedelta(day=14)
        return self.filter(due_date__gte=two_weeks_ago)