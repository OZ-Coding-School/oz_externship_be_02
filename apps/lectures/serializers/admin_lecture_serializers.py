from __future__ import annotations

from rest_framework import serializers

from apps.lectures.models.crawled_lectures import Lecture


class AdminLectureListSerializer(serializers.ModelSerializer[Lecture]):
    lecture_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = Lecture
        fields = (
            "lecture_id",
            "title",
            "instructor",
            "thumbnail_img_url",
            "platform",
            "url_link",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
