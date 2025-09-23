from typing import Any

from rest_framework import serializers


class EmailLoginSerializer(serializers.Serializer[dict[str, Any]]):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class AccessTokenSerializer(serializers.Serializer[dict[str, Any]]):
    access_token = serializers.CharField()
