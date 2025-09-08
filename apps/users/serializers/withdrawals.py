# apps/users/serializers/withdrawals.py

from typing import Any

from rest_framework import serializers

from apps.users.models.withdrawals import WithdrawalsReasonChoices


class WithdrawalRequestSerializer(serializers.Serializer[dict[str, Any]]):
    reason = serializers.ChoiceField(choices=WithdrawalsReasonChoices.choices)
    reason_detail = serializers.CharField(required=True, allow_blank=True)
