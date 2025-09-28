from typing import List

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from apps.lectures.models.categories import Category
from apps.lectures.models.crawled_lectures import Lecture


class CategorySerializer(serializers.ModelSerializer[Category]):
    class Meta:
        model = Category
        fields = ["id", "name"]


class LectureSerializer(ModelSerializer[Lecture]):
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Lecture
        fields = (
            "uuid",
            "title",
            "instructor",
            "duration",
            "description",
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
