# tests/users/test_withdrawal_service.py

import pytest
from datetime import date, timedelta
from apps.users.services.withdrawals import request_withdrawal
from apps.users.models.withdrawals import Withdrwals

@pytest.mark.django_db
def test_request_withdrawal_creates_record(user_factory):
    user = user_factory()
    data = {
        "reason": "서비스 불만",
        "details": "광고가 너무 많아요"
    }

    withdrawal = request_withdrawal(user, data)

    assert isinstance(withdrawal, Withdrwals)
    assert withdrawal.user == user
    assert withdrawal.due_date == date.today() + timedelta(days=14)
    assert withdrawal.reason == "서비스 불만"
