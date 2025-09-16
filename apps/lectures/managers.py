from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, cast

from django.db import models

if TYPE_CHECKING:
    from apps.lectures.models.crawled_lectures import Lecture
    from apps.lectures.models.lecture_bookmarks import LectureBookmark
    from apps.users.models.user import User


class LectureBookmarkQuerySet(models.QuerySet["LectureBookmark"]):
    def for_user(self, user: "User") -> "LectureBookmarkQuerySet":
        return self.filter(user=user)

    def for_lecture(self, lecture: "Lecture") -> "LectureBookmarkQuerySet":
        return self.filter(lecture=lecture)

    def for_lecture_id(self, lecture_id: int) -> "LectureBookmarkQuerySet":
        return self.filter(lecture_id=lecture_id)


class LectureBookmarkManager(models.Manager["LectureBookmark"]):
    def get_queryset(self) -> "LectureBookmarkQuerySet":
        return cast(LectureBookmarkQuerySet, super().get_queryset())

    def add_for(self, user: "User", lecture: "Lecture") -> Tuple["LectureBookmark", bool]:
        return self.get_queryset().get_or_create(user=user, lecture=lecture)

    def remove_for(self, user: "User", lecture: "Lecture") -> int:
        deleted, _ = self.get_queryset().for_user(user).for_lecture(lecture).delete()
        return int(deleted)

    def is_bookmarked(self, user: "User", lecture: "Lecture") -> bool:
        return self.get_queryset().for_user(user).for_lecture(lecture).exists()
