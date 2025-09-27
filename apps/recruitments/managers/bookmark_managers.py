from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:  # pragma: no cover
    from apps.recruitments.models.recruitment_bookmarks import RecruitmentBookmark
    from apps.recruitments.models.recruitments import Recruitment
    from apps.users.models import User


class RecruitmentBookmarkManager(models.Manager["RecruitmentBookmark"]):
    def add_bookmark(self, user: "User", recruitment: "Recruitment") -> tuple["RecruitmentBookmark", bool]:
        bookmark, created = self.get_or_create(user=user, recruitment=recruitment)
        return bookmark, created

    def remove_bookmark(self, user: "User", recruitment: "Recruitment") -> tuple[int, dict[str, int]]:
        deleted_count, _ = self.filter(user=user, recruitment=recruitment).delete()
        return deleted_count, _
