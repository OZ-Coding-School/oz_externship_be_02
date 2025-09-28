from __future__ import annotations

from typing import Any, Iterable, cast

from rest_framework import serializers

from apps.lectures.models.crawled_lectures import Lecture


class AdminLectureListSerializer(serializers.ModelSerializer[Lecture]):
    class Meta:
        model = Lecture
        fields = (
            "id",
            "title",
            "instructor",
            "thumbnail_img_url",
            "platform",
            "url_link",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class AdminLectureDetailSerializer(serializers.ModelSerializer[Lecture]):
    lecture_uuid = serializers.UUIDField(source="uuid", read_only=True)
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Lecture
        fields = (
            "lecture_uuid",
            "title",
            "instructor",
            "thumbnail_img_url",
            "description",
            "difficulty",
            "duration",
            "original_price",
            "discount_price",
            "platform",
            "url_link",
            "categories",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_categories(self, obj: Lecture) -> list[dict[str, Any]]:
        qs = obj.categories.values("id", "name")
        return list(cast(Iterable[dict[str, Any]], qs))
