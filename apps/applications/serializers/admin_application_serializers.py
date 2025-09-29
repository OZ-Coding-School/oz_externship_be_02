from apps.applications.models.applications import Application
from rest_framework import serializers

from apps.users.models.user import User


class ApplicationUserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields=("nickname", "email")

class ApplicationAdminSerializer(serializers.ModelSerializer[Application]):
    recruitment = serializers.CharField(source="recruitment")
    user=ApplicationUserSerializer(source="user")

    class Meta:
        model = Application
        fields=(
            "id",
            "recruitment",
            "user",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields