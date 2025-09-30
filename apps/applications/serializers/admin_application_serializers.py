from rest_framework import serializers

from apps.applications.models.applications import Application
from apps.recruitments.serializers.serializers_list import (
    RecruitmentApplicationSerializer,
)
from apps.users.models.user import User


# 리스트 조회 사용 시리얼라이저
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


# 상세 조회 사용 시리얼라이저
class ApplicationDetailUserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ("nickname", "gender", "profile_img_url")


class ApplicationAdminDetailSerializer(serializers.ModelSerializer[Application]):
    recruitment = RecruitmentApplicationSerializer()
    user = ApplicationDetailUserSerializer()

    class Meta:
        model = Application
        fields = (
            "id",
            "recruitment",
            "user",
            "self_introduction",
            "motivation",
            "objective",
            "available_time",
            "has_study_experience",
            "study_experience",
            "status",
            "created_at",
            "updated_at",
        )
