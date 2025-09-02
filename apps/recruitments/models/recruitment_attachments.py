from django.db import models

from apps.core.models.base import BaseModel
from apps.recruitments.models.recruitments import Recruitment


class RecruitmentAttachment(BaseModel):
    # Recruitment.attachments
    recruitment_id = models.ForeignKey(
        Recruitment,
        on_delete=models.CASCADE,
        related_name="attachments",
        null=False,
        help_text="스터디 공고 ID",
    )
    file_url = models.URLField(max_length=255, unique=True, help_text="첨부파일 URL")
    file_name = models.CharField(max_length=50, help_text="원본 파일명")

    class Meta:
        db_table = "recruitment_attachments"

    def __str__(self) -> str:
        return self.file_name
