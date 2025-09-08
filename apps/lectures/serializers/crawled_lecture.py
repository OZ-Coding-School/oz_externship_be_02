from typing import List

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from apps.lectures.models.crawled_lectures import Lecture


class LectureSerializer(ModelSerializer[Lecture]):
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Lecture
        fields = (
            "uuid",
            "title",
            "instructor",
            "updated_at",
            "average_rating",
            "categories",
            "difficulty",
            "original_price",
            "discount_price",
            "platform",
            "url_link",
            "thumbnail_img_url",
            "created_at",
        )

    def get_categories(self, obj: Lecture) -> List[int]:
        return [lc.category.id for lc in obj.lecturecategory_set.all()]
