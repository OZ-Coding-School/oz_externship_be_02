from datetime import datetime
from typing import Any, cast
from uuid import UUID

from rest_framework import serializers

from apps.applications.models import Application
from apps.recruitments.models import Recruitment
from apps.recruitments.serializers.recruitments_serializers import (
    LectureSerializer,
    TagSerializer,
)
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


class MyApplicationListSerializer(serializers.ModelSerializer[Recruitment]):
    thumbnail_image_url = serializers.SerializerMethodField()
    lectures = LectureSerializer(many=True, read_only=True, source="study_group.lectures")
    tags = TagSerializer(many=True, read_only=True)
    applied_at = serializers.DateTimeField(source="user_applied_at")
    status = serializers.CharField(source="user_application_status")

    class Meta:
        model = Recruitment
        fields = [
            "uuid",
            "title",
            "thumbnail_image_url",
            "expected_headcount",
            "lectures",
            "tags",
            "close_at",
            "applied_at",
            "status",
        ]

    def get_thumbnail_image_url(self, obj: Recruitment) -> str | None:
        if obj.images.exists():
            first_image = obj.images.first()
            if first_image:
                return first_image.img_url
        return None
