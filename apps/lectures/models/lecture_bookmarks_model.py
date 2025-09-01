from django.db import models
# IMPORT USERMODEL
from apps.lectures.models.lecture_categories_model import Lecture

class LectureBookmark(models.Model):
    # user = models.ForeignKey(
    #     User,
    #     on_delete=models.CASCADE,
    #     null=False
    # )
    # 강의 모델과의 외래키 관계 설정
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        null=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lecture_bookmarks'
        verbose_name = '강의 북마크'
        verbose_name_plural = '강의 북마크 목록'
        # unique_together = ('user', 'lecture')