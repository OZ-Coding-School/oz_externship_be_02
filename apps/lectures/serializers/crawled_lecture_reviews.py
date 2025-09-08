from rest_framework import serializers

from apps.lectures.models.crawled_lecture_reviews import LectureReview


class LectureReviewSerializer(serializers.ModelSerializer[LectureReview]):
    class Meta:
        model = LectureReview
        fields = ["lecture", "rating", "content"]
