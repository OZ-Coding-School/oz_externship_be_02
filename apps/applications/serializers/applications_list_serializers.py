from rest_framework import serializers

from apps.applications.models import Application
from apps.users.models import User


class ApplicantSerializer(serializers.ModelSerializer[User]):
    """
    지원자 정보 Serializer
    """

    class Meta:
        model = User
        fields = ["nickname", "gender", "profile_img_url"]


class RecruitmentApplicationListSerializer(serializers.ModelSerializer[Application]):
    """
    특정 공고에 대한 지원자 목록 조회 Serializer
    """

    application_id = serializers.IntegerField(source="id")
    applicant = ApplicantSerializer(source="user", read_only=True)
    applied_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Application
        fields = [
            "application_id",
            "applicant",
            "available_time",
            "has_study_experience",
            "status",
            "applied_at",
        ]
