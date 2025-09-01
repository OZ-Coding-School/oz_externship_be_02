from django.db import models

from apps.core.models import BaseModel
from apps.lectures.models.categories import Category
from apps.lectures.models.crawled_lectures import Lecture


class LectureCategory(BaseModel):
    pk = models.CompositePrimaryKey("lecture_id", "category_id")
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, null=False)

    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=False)

    class Meta:
        db_table = "lecture_categories"
        verbose_name = "강의 카테고리"
        verbose_name_plural = "강의 카테고리 목록"
