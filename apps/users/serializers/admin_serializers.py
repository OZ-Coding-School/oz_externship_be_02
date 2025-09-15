from typing import Any, cast

from rest_framework import serializers

from apps.users.models import User


class UserPermissionRequestSerializer(serializers.Serializer[Any]):
    PERMISSION_CHOICES = [
        ("general", "일반회원"),
        ("staff", "스태프"),
        ("admin", "관리자"),
    ]

    permission = serializers.ChoiceField(
        choices=PERMISSION_CHOICES,
        required=True,
        help_text="변경할 권한 (general: 일반회원, staff: 스태프, admin: 관리자)",
    )

    class Meta:
        model = User
        fields = ["is_staff", "is_superuser"]

    def save(self, **kwargs: Any) -> User:
        target_user = cast(User, self.context["target_user"])
        permission = self.validated_data["permission"]

        if permission == "admin":
            target_user.is_staff = True
            target_user.is_superuser = True
        elif permission == "staff":
            target_user.is_staff = True
            target_user.is_superuser = False
        else:
            target_user.is_staff = False
            target_user.is_superuser = False

        target_user.save(update_fields=["is_staff", "is_superuser", "updated_at"])

        return target_user


class UserPermissionResponseSerializer(serializers.ModelSerializer[User]):
    """
    아직 유저 상세 조회 API가 없어서 임시로 만들어둔 serializer
    """

    permission = serializers.SerializerMethodField()
    permission_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "nickname",
            "permission",
            "permission_display",
            "is_active",
            "updated_at",
        ]
        read_only_fields = fields

    def get_permission(self, obj: User) -> str:

        if obj.is_superuser:
            return "admin"
        elif obj.is_staff:
            return "staff"
        else:
            return "general"

    def get_permission_display(self, obj: User) -> str:
        permission = self.get_permission(obj)
        permission_map = {
            "admin": "관리자",
            "staff": "스태프",
            "general": "일반회원",
        }
        return permission_map.get(permission, "일반회원")
