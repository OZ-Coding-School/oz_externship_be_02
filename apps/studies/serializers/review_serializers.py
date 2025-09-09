from rest_framework import serializers
from apps.studies.models.study_reviews import StudyReview
from apps.studies.models.study_groups import StudyGroup


class ReviewCreateSerializer(serializers.ModelSerializer):
    """
    스터디 리뷰 작성 Serializer
    - 종료된 스터디 그룹만 리뷰 가능
    - 한 유저가 같은 스터디 그룹에 중복 리뷰 작성 불가
    """

    study_group_id = serializers.PrimaryKeyRelatedField(
        queryset=StudyGroup.objects.all(),
        source="study_group",
        write_only=True
    )
    
    rating = serializers.ChoiceField(
        choices=StudyReview.RatingEnum.choices,
        source="star_rating"
    )
    
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = StudyReview
        fields = ["id", "user_id", "study_group_id", "rating", "content", "created_at"]
        read_only_fields = ["id", "user_id", "created_at"]

    def validate(self, attrs):
        user = self.context["request"].user
        study_group = attrs["study_group"]

        if study_group.status != StudyGroup.StatusChoices.ENDED:
            raise serializers.ValidationError(
                {"study_group_id": ["종료되지 않은 스터디 그룹에는 리뷰를 작성할 수 없습니다."]}
            )

        if StudyReview.objects.filter(user=user, study_group=study_group).exists():
            raise serializers.ValidationError(
                {"study_group_id": ["이미 리뷰를 작성한 스터디 그룹입니다."]}
            )

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        return StudyReview.objects.create(user=user, **validated_data)

