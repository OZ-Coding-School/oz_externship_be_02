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
    uuid = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    thumbnail_image_url = serializers.SerializerMethodField()
    expected_headcount = serializers.SerializerMethodField()
    lectures = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    close_at = serializers.SerializerMethodField()
    applied_at = serializers.DateTimeField(source="created_at", read_only=True)

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

    def get_uuid(self, obj: Application) -> UUID | None:
        return obj.recruitment.uuid if obj.recruitment else None

    def get_title(self, obj: Application) -> str | None:
        return obj.recruitment.title if obj.recruitment else None

    def get_thumbnail_image_url(self, obj: Application) -> str | None:
        if obj.recruitment and obj.recruitment.images.exists():
            first_image = obj.recruitment.images.first()
            if first_image:
                return first_image.img_url
        return None

    def get_expected_headcount(self, obj: Application) -> int | None:
        return obj.recruitment.expected_headcount if obj.recruitment else None

    def get_lectures(self, obj: Application) -> list[dict[str, Any]]:
        if obj.recruitment:
            return cast(list[dict[str, Any]], LectureSerializer(obj.recruitment.study_group.lectures, many=True).data)
        return []

    def get_tags(self, obj: Application) -> list[dict[str, Any]]:
        if obj.recruitment:
            return cast(list[dict[str, Any]], TagSerializer(obj.recruitment.tags, many=True).data)
        return []

    def get_close_at(self, obj: Application) -> datetime | None:
        return obj.recruitment.close_at if obj.recruitment else None
