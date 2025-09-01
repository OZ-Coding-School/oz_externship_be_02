from django.db import models
# IMPORT USERMODEL
from apps.lectures.models.categories_model import CategoryModel

class UserPreferCategoryModel(models.Model):
    # user = models.ForeignKey(
    #     User,
    #     on_delete=models.CASCADE,
    #     null=False,
    # )
    category = models.ForeignKey(
        CategoryModel,
        on_delete=models.CASCADE,
        null=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_prefer_categories'
        # unique_together = ('user', 'category')
        verbose_name = '사용자 선호 카테고리'
        verbose_name_plural = '사용자 선호 카테고리 목록'