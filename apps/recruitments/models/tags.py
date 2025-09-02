from django.db import models

from apps.core.models.base import BaseModel


class Tag(BaseModel):
    name = models.CharField(max_length=20, help_text="태그명")

    # ManyToManyField with Recruitment
    # tag.recruitments.all() 사용 가능

    class Meta:
        db_table = "tags"

    def __str__(self) -> str:
        return self.name
