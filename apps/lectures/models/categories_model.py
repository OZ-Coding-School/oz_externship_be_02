from django.db import models

class CategoryModel(models.Model):
    name = models.CharField(max_length=255, unique=True, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name = '강의 카테고리'
        verbose_name_plural = '강의 카테고리 목록'

    def __str__(self):
        return self.name