from django.db import models

from apps.core.models import BaseModel
from apps.lectures.models.categories import Category
from apps.users.models.user import User


class UserPreferCategory(BaseModel):
    pk = models.CompositePrimaryKey("user_id", "category_id")
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

    class Meta:
        db_table = "user_prefer_categories"
