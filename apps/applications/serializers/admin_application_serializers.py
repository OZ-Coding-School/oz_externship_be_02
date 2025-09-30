from rest_framework import serializers

from apps.applications.models.applications import Application
from apps.users.models.user import User


class ApplicationUserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ("nickname", "email")


class ApplicationAdminSerializer(serializers.ModelSerializer[Application]):
    recruitment_title = serializers.CharField(source="recruitment")
    user = ApplicationUserSerializer()

    class Meta:
        model = Application
        fields = (
            "id",
            "recruitment_title",
            "user",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
