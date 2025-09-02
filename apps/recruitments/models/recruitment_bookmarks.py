from django.db import models

from apps.core.models.base import BaseModel
from apps.recruitments.models.recruitments import Recruitment
from apps.users.models.user import User


# User - Recruitment 다대다 중간 테이블
class RecruitmentBookmark(BaseModel):
    pk = models.CompositePrimaryKey("user_id", "recruitment_id")

    user_id = models.ForeignKey(User, on_delete=models.CASCADE, help_text="북마크한 유저 ID")
    recruitment_id = models.ForeignKey(Recruitment, on_delete=models.CASCADE, help_text="공고 ID")

    class Meta:
        db_table = "recruitment_bookmarks"

    def __str__(self) -> str:
        return f"{self.user_id.nickname} bookmarks {self.recruitment_id.title}"
