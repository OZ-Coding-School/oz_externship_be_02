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


class ReviewListRequestSerializer(serializers.Serializer[Dict[str, Any]]):
    """
    스터디 그룹 리뷰 목록 조회 요청 전용 Serializer
    """

    group_uuid = serializers.UUIDField()

    def validate_group_uuid(self, value: Any) -> Any:
        # group_uuid가 유효한 StudyGroup인지 검증, 없으면 404 반환
        try:
            group = StudyGroup.objects.get(uuid=value)
        except StudyGroup.DoesNotExist as exc:
            raise NotFound(detail="해당 스터디 그룹이 존재하지 않습니다.") from exc

        self.context["study_group"] = group
        return value

    def get_queryset(self) -> QuerySet[StudyReview]:
        # 검증된 StudyGroup에 속한 리뷰 목록을 최신순으로 조회, 없으면 404 반환
        group: StudyGroup = self.context["study_group"]
        qs = StudyReview.objects.filter(study_group=group).order_by("-created_at")
        if not qs.exists():
            raise NotFound("해당 스터디 그룹에 대한 리뷰가 존재하지 않습니다.")
        return qs

    def build_payload(self) -> Dict[str, Any]:
        # 응답에 필요한 데이터(study_group_id, reviews) 구성
        group: StudyGroup = self.context["study_group"]
        reviews = self.get_queryset()
        return {"study_group_id": group.id, "reviews": reviews}


class ReviewListItemSerializer(serializers.ModelSerializer[StudyReview]):
    """
    스터디 그룹 리뷰 목록의 개별 응답 Serializer
    """

    rating = serializers.SerializerMethodField()

    class Meta:
        model = StudyReview
        fields = ["rating", "content", "created_at"]

    def get_rating(self, obj: StudyReview) -> str:
        # star_rating을 "N_OUT_OF_5_STARS" 포맷으로 변환
        return f"{int(obj.star_rating)}_OUT_OF_5_STARS"


class ReviewListResponseSerializer(serializers.Serializer[Dict[str, Any]]):
    """
    스터디 그룹 리뷰 목록 응답 Envelope Serializer
    """

    study_group_id = serializers.IntegerField()
    reviews = ReviewListItemSerializer(many=True)
