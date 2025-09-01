from django.db import models
from apps.users.models.user import User
from apps.lectures.models.categories_model import Category

class UserPreferCategory(models.Model):
    user = models.ForeignKey(
         User,
         on_delete=models.CASCADE,
         null=False,
     )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_prefer_categories'
        unique_together = ('user', 'category')
        verbose_name = '사용자 선호 카테고리'
        verbose_name_plural = '사용자 선호 카테고리 목록'