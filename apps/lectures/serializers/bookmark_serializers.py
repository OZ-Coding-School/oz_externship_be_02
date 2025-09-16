from __future__ import annotations

from typing import TypedDict

from rest_framework import serializers


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
