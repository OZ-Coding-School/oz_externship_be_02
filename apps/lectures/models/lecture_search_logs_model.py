from django.db import models
# IMPORT USERMODEL

class LectureSearchLog(models.Model):
    # user = models.ForeignKey(
    #     User,
    #     on_delete=models.CASCADE,
    #     null=False,
    #     related_name='search_logs'
    # )
    keyword = models.CharField(max_length=255, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lecture_search_logs'
        verbose_name = '강의 검색 기록'
        verbose_name_plural = '강의 검색 기록 목록'