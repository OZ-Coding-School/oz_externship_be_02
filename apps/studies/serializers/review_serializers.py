from typing import Any, Dict

from django.db.models import QuerySet
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.validators import UniqueTogetherValidator

from apps.studies.models.study_groups import StudyGroup
from apps.studies.models.study_reviews import StudyReview
from apps.users.models.user import User


# 요청 전용 Serializer
class ReviewCreateRequestSerializer(serializers.ModelSerializer[StudyReview]):
    """
    스터디 리뷰 작성 Request Serializer
    - 클라이언트가 보내는 값만 포함
    """

    star_rating = serializers.ChoiceField(
        choices=StudyReview.RatingEnum.choices,
        write_only=True,
    )

    class Meta:
        model = StudyReview
        fields = ["star_rating", "content"]

        extra_kwargs = {
            "content": {"write_only": True},
            "star_rating": {"write_only": True},
        }


# 응답 전용 Serializer
class ReviewCreateResponseSerializer(serializers.ModelSerializer[StudyReview]):
    """
    스터디 리뷰 작성 Response Serializer
    - 서버가 클라이언트에게 돌려주는 값만 포함
    """

    study_group_uuid = serializers.IntegerField(source="study_group.uuid")

    class Meta:
        model = StudyReview
        fields = ["id", "user_id", "study_group_uuid", "star_rating", "content", "created_at"]
        read_only_fields = fields


class ReviewListResponseSerializer(serializers.ModelSerializer[StudyReview]):
    """
    스터디 그룹 리뷰 목록의 개별 응답 Serializer
    """

    study_group_uuid = serializers.UUIDField(source="study_group.uuid", read_only=True)

    class Meta:
        model = StudyReview
        fields = ["study_group_uuid", "star_rating", "content", "created_at"]


class ReviewUpdateRequestSerializer(serializers.ModelSerializer[StudyReview]):
    class Meta:  # 리뷰 수정 요청전용 시리얼라이져
        model = StudyReview
        fields = ["star_rating", "content"]
        extra_kwargs = {
            "star_rating": {"required": False},
            "content": {"required": False},
        }


class ReviewUpdateResponseSerializer(serializers.ModelSerializer[StudyReview]):

    study_group_uuid = serializers.UUIDField(source="study_group.uuid", read_only=True)
    user_uuid = serializers.UUIDField(source="user.uuid", read_only=True)

    class Meta:  # 리뷰 수정 응답전용 시리얼라이져
        model = StudyReview
        fields = [
            "id",
            "user_uuid",
            "study_group_uuid",
            "star_rating",
            "content",
            "updated_at",
        ]
