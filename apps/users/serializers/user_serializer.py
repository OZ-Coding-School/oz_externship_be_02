from typing import Any

from rest_framework import serializers


class VerificationSerializer(serializers.Serializer): # type: ignore
    email = serializers.EmailField(required=True)
    verification_code = serializers.CharField(required=True)
