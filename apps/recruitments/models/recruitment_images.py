from django.db import models

from apps.core.models.base import BaseModel
from apps.recruitments.models.recruitments import Recruitment


class RecruitmentImage(BaseModel):
    # Recruitment.images
    recruitment = models.ForeignKey(
        Recruitment, on_delete=models.CASCADE, related_name="images", help_text="스터디 공고 ID"
    )
    img_url = models.URLField(max_length=255, unique=True, help_text="이미지 URL")

    class Meta:
        db_table = "recruitment_images"

    def __str__(self) -> str:
        return f"Image for {self.recruitment.title}"
