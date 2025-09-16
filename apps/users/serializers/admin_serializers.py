from typing import Any, Dict

from rest_framework import serializers

from apps.users.models import User, Withdrawals


class UserPermissionUpdateSerializer(serializers.Serializer[Any]):
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

    def to_internal_value(self, data: Dict[str, Any]) -> Any:
        """
        입력 데이터를 내부 값으로 변환하기 전에 처리
        """
        # 'permission' 필드가 있으면 소문자로 변환
        if "permission" in data and isinstance(data["permission"], str):
            data["permission"] = data["permission"].lower()

        return super().to_internal_value(data)

    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        permission = validated_data.get("permission")
        request = self.context.get("request")
        # admin이 자기 자신의 권한을 더 낮은 권한으로 변경할 수 없도록 방지
        if request and request.user == instance and instance.is_superuser and permission != "admin":
            raise serializers.ValidationError({"error": "자신의 최고 관리자 권한은 해제할 수 없습니다."})

        # admin은 최소 1명 이상 존재해야하므로 0명이 되지 않도록 방지
        if instance.is_superuser and permission != "admin" and User.objects.filter(is_superuser=True).count() <= 1:
            raise serializers.ValidationError({"error": "최소 한 명의 최고 관리자 시스템에 존재해야 합니다."})

        if permission == "admin":
            instance.is_staff = True
            instance.is_superuser = True
        elif permission == "staff":
            instance.is_staff = True
            instance.is_superuser = False
        else:
            instance.is_staff = False
            instance.is_superuser = False

        instance.save(update_fields=["is_staff", "is_superuser", "updated_at"])
        return instance


class UserPermissionResponseSerializer(serializers.ModelSerializer[User]):
    """
    아직 유저 상세 조회 API가 없어서 임시로 만들어둔 serializer
    """

    permission = serializers.SerializerMethodField()
    permission_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "uuid",
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


# 회원 목록 조회 시리얼라이저
class UserAdminListSerializer(serializers.ModelSerializer[User]):
    permission = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    withdrawals_request_date = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "uuid",
            "email",
            "nickname",
            "name",
            "birthday",
            "permission",
            "status",
            "created_at",
            "withdrawals_request_date",
        ]

    def get_permission(self, obj: User) -> str:
        if obj.is_superuser:
            return "admin"
        if obj.is_staff:
            return "staff"
        return "general"

    def get_status(self, obj: User) -> str:
        if hasattr(obj, "withdrawals") and obj.withdrawals:
            return "탈퇴진행중"
        return "활성화" if obj.is_active else "비활성화"

    # Withdrawals 객체가 존재하면, 해당 객체의 생성일(탈퇴요청일) 반환
    def get_withdrawals_request_date(self, obj: User) -> str | None:
        if hasattr(obj, "withdrawals") and obj.withdrawals:
            return obj.withdrawals.created_at.isoformat()
        return None
