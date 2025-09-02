from django.db import models

from apps.core.models.base import BaseModel
from apps.users.models.user import User


class RecruitmentSearchLog(BaseModel):
    # User.recruitment_search_logs
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recruitment_search_logs", help_text="유저 ID"
    )
    keyword = models.CharField(max_length=255, help_text="검색어")

    class Meta:
        db_table = "recruitment_search_logs"

    def __str__(self) -> str:
        return f"'{self.keyword}' by {self.user.nickname}"
