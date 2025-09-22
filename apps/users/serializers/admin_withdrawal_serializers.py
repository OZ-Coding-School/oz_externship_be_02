from rest_framework import serializers

from apps.users.models import Withdrawals
from apps.users.utils.enums import Permission, UserStatus


class AdminWithdrawalListSerializer(serializers.ModelSerializer[Withdrawals]):
    email = serializers.SerializerMethodField(help_text="탈퇴 유저 이메일")
    name = serializers.SerializerMethodField(help_text="탈퇴 유저 이름")
    permission = serializers.SerializerMethodField(help_text="탈퇴 유저 권한")
    birthday = serializers.SerializerMethodField(help_text="탈퇴 유저 생년월일")

    class Meta:
        model = Withdrawals
        fields = [
            "id",
            "email",
            "name",
            "permission",
            "birthday",
            "reason",
            "created_at",
        ]

    def get_email(self, obj: Withdrawals) -> str:
        return obj.user.email

    def get_name(self, obj: Withdrawals) -> str:
        return obj.user.name

    def get_permission(self, obj: Withdrawals) -> str:
        return Permission.from_user(obj.user).value[0]

    def get_birthday(self, obj: Withdrawals) -> str:
        return obj.user.birthday.isoformat()


class AdminWithdrawalDetailSerializer(serializers.ModelSerializer[Withdrawals]):
    name = serializers.CharField(source="user.name", read_only=True)
    gender = serializers.CharField(source="user.gender", read_only=True)
    nickname = serializers.CharField(source="user.nickname", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    permission = serializers.SerializerMethodField(help_text="탈퇴 유저 권한")
    status = serializers.SerializerMethodField(help_text="탈퇴 유저 상태")
    user_joined_at = serializers.DateTimeField(source="user.created_at", read_only=True)
    profile_img_url = serializers.URLField(source="user.profile_img_url", read_only=True)

    class Meta:
        model = Withdrawals
        fields = [
            "id",
            "name",
            "gender",
            "nickname",
            "email",
            "permission",
            "status",
            "user_joined_at",
            "profile_img_url",
            "created_at",
            "reason",
            "reason_detail",
            "due_date",
        ]

    def get_permission(self, obj: Withdrawals) -> str:
        return Permission.from_user(obj.user).value[0]

    def get_status(self, obj: Withdrawals) -> str:
        return UserStatus.WITHDRAWN.value[1]
