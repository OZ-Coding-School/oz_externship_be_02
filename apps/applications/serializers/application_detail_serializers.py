from rest_framework import serializers

from apps.applications.models import Application
from apps.users.models import User


class _ApplicantInfoSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["nickname", "gender", "profile_img_url"]


class ApplicationDetailSerializer(serializers.ModelSerializer[Application]):
    applicant_info = _ApplicantInfoSerializer(source="user", read_only=True)
    introduction = serializers.CharField(source="self_introduction", read_only=True)
    study_goal = serializers.CharField(source="objective", read_only=True)
    available_times = serializers.CharField(source="available_time", read_only=True)
    specific_experience = serializers.CharField(source="study_experience", read_only=True)
    applied_at = serializers.DateTimeField(source="created_at", read_only=True, format="%Y-%m-%d %H:%M")

    class Meta:
        model = Application
        fields = [
            "id",
            "applicant_info",
            "introduction",
            "motivation",
            "study_goal",
            "available_times",
            "has_study_experience",
            "specific_experience",
            "status",
            "applied_at",
        ]


# 나의 지원내역 상세 조회
class MyApplicationDetailSerializer(serializers.ModelSerializer[Application]):
    recruitment_title = serializers.CharField(source="recruitment.title", read_only=True)
    applied_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "recruitment_title",
            "self_introduction",
            "motivation",
            "objective",
            "available_time",
            "has_study_experience",
            "study_experience",
            "status",
            "applied_at",
        ]
