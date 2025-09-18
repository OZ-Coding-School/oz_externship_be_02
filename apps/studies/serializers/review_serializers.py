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

    study_group_id = serializers.PrimaryKeyRelatedField(
        queryset=StudyGroup.objects.all(),
        source="study_group",
        write_only=True,
    )
    rating = serializers.ChoiceField(
        choices=StudyReview.RatingEnum.choices,
        source="star_rating",
        write_only=True,
    )

    # 내부 Hidden 필드
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = StudyReview
        fields = ["user", "study_group_id", "rating", "content"]

        extra_kwargs = {"content": {"write_only": True}}
        validators = [
            UniqueTogetherValidator(
                queryset=StudyReview.objects.all(),
                fields=["user", "study_group_id"],
                message="이미 리뷰를 작성한 스터디 그룹입니다.",
            )
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        study_group = attrs["study_group"]
        if study_group.status != StudyGroup.StatusChoices.ENDED:
            raise serializers.ValidationError({"detail": "종료되지 않은 스터디 그룹에는 리뷰를 작성할 수 없습니다."})
        return attrs


# 응답 전용 Serializer
class ReviewCreateResponseSerializer(serializers.ModelSerializer[StudyReview]):
    """
    스터디 리뷰 작성 Response Serializer
    - 서버가 클라이언트에게 돌려주는 값만 포함
    """

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    study_group_id = serializers.IntegerField(source="study_group.id", read_only=True)
    rating = serializers.IntegerField(source="star_rating")

    class Meta:
        model = StudyReview
        fields = ["id", "user_id", "study_group_id", "rating", "content", "created_at"]
        read_only_fields = ["id", "user_id", "study_group_id", "created_at"]


class ReviewListItemSerializer(serializers.ModelSerializer[StudyReview]):
    """
    스터디 그룹 리뷰 목록의 개별 응답 Serializer
    """

    rating = serializers.SerializerMethodField()

    class Meta:
        model = StudyReview
        fields = ["rating", "content", "created_at"]

    def get_rating(self, obj: Any) -> str:
        # star_rating을 "N_OUT_OF_5_STARS" 포맷으로 변환
        return f"{int(obj.star_rating)}_OUT_OF_5_STARS"


class ReviewListResponseSerializer(serializers.Serializer[dict[str, object]]):
    """
    스터디 그룹 리뷰 목록 응답 Envelope Serializer
    """

    study_group_id = serializers.IntegerField()
    reviews = ReviewListItemSerializer(many=True)
