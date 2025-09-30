from typing import Any

from rest_framework import serializers

from apps.users.models import User


class EmailLoginRequestSerializer(serializers.Serializer[dict[str, Any]]):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "nickname",
            "name",
            "birthday",
            "gender",
            "is_active",
            "is_staff",
            "is_superuser",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"password": {"write_only": True}}
