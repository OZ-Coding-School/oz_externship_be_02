from __future__ import annotations

from typing import Any, TypedDict, cast

from rest_framework import serializers

from apps.lectures.models.crawled_lectures import DifficultyChoices, Lecture
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
    difficulty = serializers.ChoiceField(choices=DifficultyChoices.choices, read_only=True)
    difficulty_display = serializers.CharField(source="get_difficulty_display", read_only=True)

    class Meta:
        model = Lecture
        fields = (
            "lecture_uuid",
            "title",
            "instructor",
            "thumbnail_img_url",
            "platform",
            "difficulty",
            "difficulty_display",
            "duration",
            "duration_hhmm",
            "original_price",
            "discount_price",
            "url_link",
        )

    def get_duration_hhmm(self, obj: Lecture) -> str:
        return _minutes_to_hhmm(int(obj.duration or 0))


class LectureBookmarkListSerializer(serializers.ModelSerializer[LectureBookmark]):
    lecture = BookmarkLectureSerializer()

    class Meta:
        model = LectureBookmark
        fields = ["user_id", "lecture"]
