from __future__ import annotations

from typing import Any, TypedDict

from rest_framework import serializers

from apps.lectures.models.crawled_lectures import Lecture


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


# 북마크 목록 조회(REQ-LECT-006)
class BookmarkListItemSerializer(serializers.ModelSerializer[Lecture]):
    duration_hhmm = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()  # 변환 필드

    class Meta:
        model = Lecture
        fields = (
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
