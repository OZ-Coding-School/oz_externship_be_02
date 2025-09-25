from __future__ import annotations

from typing import Any, TypedDict, cast

from rest_framework import serializers

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_bookmarks import LectureBookmark


class BookmarkToggleRequest(TypedDict):
    lecture_id: int


class BookmarkToggleResponse(TypedDict):
    lecture_id: int
    bookmarked: bool


class BookmarkToggleRequestSerializer(serializers.Serializer[BookmarkToggleRequest]):
    lecture_id = serializers.IntegerField()


class BookmarkToggleResponseSerializer(serializers.Serializer[BookmarkToggleResponse]):
    lecture_id = serializers.IntegerField()
    bookmarked = serializers.BooleanField()


def _minutes_to_hhmm(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


class BookmarkLectureSerializer(serializers.ModelSerializer[Lecture]):
    lecture_uuid = serializers.UUIDField(source="uuid", read_only=True)
    duration_hhmm = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()

    class Meta:
        model = Lecture
        fields = (
            "lecture_uuid",
            "title",
            "instructor",
            "thumbnail_img_url",
            "platform",
            "difficulty",
            "duration_hhmm",
            "original_price",
            "discount_price",
            "url_link",
        )

    def get_duration_hhmm(self, obj: Lecture) -> str:
        return _minutes_to_hhmm(int(obj.duration or 0))

    def get_difficulty(self, obj: Lecture) -> str:
        raw = (obj.difficulty or "").upper()
        return "MIDDLE" if raw == "NORMAL" else raw


class LectureBookmarkListSerializer(serializers.ModelSerializer[LectureBookmark]):
    lecture = BookmarkLectureSerializer()

    class Meta:
        model = LectureBookmark
        fields = ("lecture",)

    def to_representation(self, instance: LectureBookmark) -> dict[str, Any]:
        base: dict[str, Any] = super().to_representation(instance)
        lecture_data = base.get("lecture")
        return lecture_data if isinstance(lecture_data, dict) else {}
