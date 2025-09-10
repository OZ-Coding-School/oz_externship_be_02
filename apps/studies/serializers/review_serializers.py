from typing import Any

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.studies.models.study_groups import StudyGroup
from apps.studies.models.study_reviews import StudyReview


class ReviewCreateSerializer(serializers.ModelSerializer[StudyReview]):
    """
    스터디 리뷰 작성 Serializer
    - 종료된 스터디 그룹만 리뷰 가능
    - 한 유저가 같은 스터디 그룹에 중복 리뷰 작성 불가
    """

    # 요청에서 받는 필드
    study_group_id = serializers.PrimaryKeyRelatedField(
        queryset=StudyGroup.objects.all(), source="study_group", write_only=True
    )
    rating = serializers.ChoiceField(choices=StudyReview.RatingEnum.choices, source="star_rating")

    # 응답 전용
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    # 내부 Hidden 필드
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    study_group = serializers.HiddenField(default=None)

    class Meta:
        model = StudyReview
        fields = ["id", "user", "user_id", "study_group", "study_group_id", "rating", "content", "created_at"]
        read_only_fields = ["id", "user_id", "created_at"]

        extra_kwargs = {
            "user": {"write_only": True},
            "study_group": {"write_only": True},  # 응답에서 숨김
        }
        validators = [  # 코치님 피드백 반영: user + study_group 중복 검증은 UniqueTogetherValidator로 처리
            UniqueTogetherValidator(
                queryset=StudyReview.objects.all(),
                fields=["user", "study_group"],
                message="이미 리뷰를 작성한 스터디 그룹입니다.",
            )
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        study_group = attrs["study_group"]
        if study_group.status != StudyGroup.StatusChoices.ENDED:
            raise serializers.ValidationError(
                {"study_group_id": ["종료되지 않은 스터디 그룹에는 리뷰를 작성할 수 없습니다."]}
            )
        return attrs

    def create(self, validated_data: dict[str, Any]) -> StudyReview:
        return StudyReview.objects.create(**validated_data)
