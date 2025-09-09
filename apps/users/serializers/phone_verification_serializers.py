from typing import Any

from rest_framework import serializers


# 인증번호 전송
class PhoneVerificationSerializer(serializers.Serializer[Any]):
    phone_number = serializers.CharField(max_length=20, required=True)


# 인증번호 검증
class VerifyCodeSerializer(serializers.Serializer[Any]):
    phone_number = serializers.CharField(max_length=20, required=True)
    verification_code = serializers.CharField(max_length=6, min_length=6, required=True)
