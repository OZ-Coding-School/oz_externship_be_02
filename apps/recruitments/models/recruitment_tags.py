from django.db import models

from apps.core.models.base import BaseModel
from apps.recruitments.models.recruitments import Recruitment
from apps.recruitments.models.tags import Tag


# Recruitment - Tag 다대다 중간 테이블
class RecruitmentTag(BaseModel):
    pk = models.CompositePrimaryKey("recruitment", "tag")

    recruitment = models.ForeignKey(Recruitment, on_delete=models.CASCADE, help_text="공고 ID")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, help_text="태그 ID")

    # id = None  # 자동 생성되는 PK 제거

    class Meta:
        db_table = "recruitment_tags"
        # Django가 id 자동 생성 안 하도록 기본 PK 설정
        # managed = True

    def __str__(self) -> str:
        return f"{self.recruitment.title} - {self.tag.name}"
