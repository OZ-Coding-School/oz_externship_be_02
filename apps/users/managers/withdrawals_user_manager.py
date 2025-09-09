import datetime
from datetime import timedelta
from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone

if TYPE_CHECKING:
    from apps.users.models.withdrawals import Withdrawals


class WithdrawalUserManager(models.Manager["Withdrawals"]):
    # 2주 내에 탈퇴한 유저
    def recently_withdrawn(self) -> models.QuerySet["Withdrawals"]:
        two_weeks_ago = timezone.now() - datetime.timedelta(weeks=2)
        return self.filter(due_date__gte=two_weeks_ago)
