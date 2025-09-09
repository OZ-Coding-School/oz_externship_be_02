from typing import Any

from rest_framework import serializers


class EmailVerificationRequestSerializer(serializers.Serializer[dict[str, Any]]):
    email = serializers.EmailField(required=True)


class EmailVerifyCodeSerializer(serializers.Serializer[dict[str, Any]]):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, max_length=6)
