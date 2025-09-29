from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from apps.lectures.models.crawled_lecture_reviews import LectureReview


class LectureReviewSerializer(ModelSerializer[LectureReview]):
    lecture = serializers.UUIDField(source="lecture.uuid", read_only=True)

    class Meta:
        model = LectureReview
        fields = (
            "lecture",
            "rating",
            "content",
        )
