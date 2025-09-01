from django.db import models
from apps.lectures.models.crawled_lectures_model import LectureModel
from apps.lectures.models.categories_model import CategoryModel


class LectureCategoryModel(models.Model):
    lecture = models.ForeignKey(
        LectureModel,
        on_delete=models.CASCADE, # 동반 자살
        null=False
    )
    category = models.ForeignKey(
        CategoryModel,
        on_delete=models.CASCADE,
        null=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lecture_categories'
        verbose_name = '강의 카테고리'
        verbose_name_plural = '강의 카테고리 목록'
        unique_together = ('lecture', 'category') # 잉덱싱, 복합히 역할