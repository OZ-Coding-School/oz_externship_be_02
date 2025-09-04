from django.db import models

from apps.core.models import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=255, unique=True, null=False)

    class Meta:
        db_table = "categories"

    def __str__(self) -> str:
        return self.name
