from datetime import datetime
from typing import Any, cast
from uuid import UUID

from rest_framework import serializers

from apps.applications.models import Application
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


class MyApplicationListSerializer(serializers.ModelSerializer[Application]):
    uuid = serializers.CharField(source="recruitment.uuid")
    title = serializers.CharField(source="recruitment.title")
    thumbnail_image_url = serializers.SerializerMethodField()
    expected_headcount = serializers.IntegerField(source="recruitment.expected_headcount")
    lectures = LectureSerializer(many=True, read_only=True, source="recruitment.study_group.lectures")
    tags = TagSerializer(many=True, read_only=True, source="recruitment.tags")
    close_at = serializers.DateTimeField(source="recruitment.close_at")
    applied_at = serializers.DateTimeField(source="created_at", read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Application
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

    def get_thumbnail_image_url(self, obj: Application) -> str | None:
        if obj.recruitment and obj.recruitment.images.exists():
            first_image = obj.recruitment.images.first()
            if first_image:
                return first_image.img_url
        return None
