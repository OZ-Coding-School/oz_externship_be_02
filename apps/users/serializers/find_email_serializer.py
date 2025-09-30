# apps/users/serializers/find_email_serializer.py

from typing import Any, Dict

from rest_framework import serializers

from apps.users.services.phone_service import TwilioAuthService

phone_service = TwilioAuthService()


class PhoneVerificationCodeSerializer(serializers.Serializer[Dict[str, Any]]):
    name = serializers.CharField(max_length=10)
    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6, required=True, allow_blank=False)
