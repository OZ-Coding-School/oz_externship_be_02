# apps/users/serializers/find_email_serializer.py

from typing import Any, Dict

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.users.services.phone_service import (
    PhoneVerificationCodeFailedError,
    PhoneVerificationService,
    TwilioAuthService,
)
from apps.users.utils.enums import VerificationPurpose

phone_service = TwilioAuthService()


class PhoneVerificationCodeSerializer(serializers.Serializer[Dict[str, Any]]):
    name = serializers.CharField(max_length=10)
    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6, required=True, allow_blank=False)
