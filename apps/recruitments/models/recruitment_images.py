from django.db import models

from apps.core.models.base import BaseModel
from apps.recruitments.models.recruitments import Recruitment


class RecruitmentImage(BaseModel):
    # Recruitment.images
    recruitment_id = models.ForeignKey(
        Recruitment, on_delete=models.CASCADE, related_name="images", null=False, help_text="스터디 공고 ID"
    )
    img_url = models.CharField(max_length=255, unique=True, null=False, help_text="이미지 URL")

    class Meta:
        db_table = "recruitment_images"

    def __str__(self):
        return f"Image for {self.recruitment_id.title}"
