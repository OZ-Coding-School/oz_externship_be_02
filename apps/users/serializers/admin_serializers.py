from typing import Any, Dict, Union

from rest_framework import serializers

from apps.users.models import User
from apps.users.utils.enums import Permission


class UserPermissionUpdateSerializer(serializers.ModelSerializer[User]):
    PERMISSION_CHOICES = [(p.name, p.value) for p in Permission]

    permission = serializers.ChoiceField(
        choices=PERMISSION_CHOICES,
        required=True,
        write_only=True,
        help_text="변경할 권한 (general: 일반회원, staff: 스태프, admin: 관리자)",
    )

    class Meta:
        model = User
        fields = ["permission"]

    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        permission = validated_data.get("permission")
        request = self.context.get("request")
        # admin이 자기 자신의 권한을 더 낮은 권한으로 변경할 수 없도록 방지
        if request and request.user == instance and instance.is_superuser and permission != Permission.ADMIN.name:
            raise serializers.ValidationError({"error": "자신의 최고 관리자 권한은 해제할 수 없습니다."})

        # admin은 최소 1명 이상 존재해야하므로 0명이 되지 않도록 방지
        if (
            instance.is_superuser
            and permission != Permission.ADMIN.name
            and User.objects.filter(is_superuser=True).count() <= 1
        ):
            raise serializers.ValidationError({"error": "최소 한 명의 최고 관리자 시스템에 존재해야 합니다."})

        if permission == Permission.ADMIN.name:
            instance.is_staff = True
            instance.is_superuser = True
        elif permission == Permission.STAFF.name:
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

    def get_permission(self, obj: User) -> Union[str, None]:
        return getattr(Permission.from_user(obj), "name", None)

    def get_permission_display(self, obj: User) -> Union[str, None]:
        return getattr(Permission.from_user(obj), "value", None)


# 회원 목록 조회 시리얼라이저
class UserAdminListSerializer(serializers.ModelSerializer[User]):
    permission = serializers.SerializerMethodField()
    permission_display = serializers.SerializerMethodField()
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
            "permission_display",
            "status",
            "created_at",
            "withdrawals_request_date",
        ]

    def get_permission(self, obj: User) -> Union[str, None]:
        return getattr(Permission.from_user(obj), "name", None)

    def get_permission_display(self, obj: User) -> Union[str, None]:
        return getattr(Permission.from_user(obj), "value", None)

    def get_status(self, obj: User) -> str:
        if hasattr(obj, "withdrawals") and obj.withdrawals:
            return "탈퇴진행중"
        return "활성화" if obj.is_active else "비활성화"

    # Withdrawals 객체가 존재하면, 해당 객체의 생성일(탈퇴요청일) 반환
    def get_withdrawals_request_date(self, obj: User) -> str | None:
        if hasattr(obj, "withdrawals") and obj.withdrawals:
            return obj.withdrawals.created_at.isoformat()
        return None

    # 회원 상세 조회용 시리얼라이저


class UserAdminDetailSerializer(serializers.ModelSerializer[User]):
    permission = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "uuid",
            "name",
            "gender",
            "nickname",
            "birthday",
            "phone_number",
            "email",
            "permission",
            "status",
            "created_at",
            "profile_img_url",
        ]

    def get_permission(self, obj: User) -> Union[str, None]:
        return getattr(Permission.from_user(obj), "name", None)

    def get_status(self, obj: User) -> str:
        if hasattr(obj, "withdrawals") and obj.withdrawals:
            return "탈퇴진행중"
        return "활성화" if obj.is_active else "비활성화"


# 회원 정보 수정 시리얼라이저
class UserAdminUpdateSerializer(serializers.ModelSerializer[User]):
    status = serializers.ChoiceField(choices=[("active", "활성화"), ("inactive", "비활성화")], write_only=True)

    class Meta:
        model = User
        fields = [
            "name",
            "gender",
            "nickname",
            "phone_number",
            "status",
            "profile_img_url",
        ]

    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        if "status" in validated_data:
            status = validated_data.get("status")
            instance.is_active = status == "active"

        return super().update(instance, validated_data)
