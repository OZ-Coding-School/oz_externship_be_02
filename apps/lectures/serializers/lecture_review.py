from rest_framework.serializers import ModelSerializer

from apps.lectures.models.crawled_lecture_reviews import LectureReview


class LectureReviewSerializer(ModelSerializer[LectureReview]):
    class Meta:
        model = LectureReview
        fields = (
            "lecture",
            "rating",
            "content",
        )
