import uuid

from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="수정 일시")

    class Meta:
        abstract = True


class UUIDBaseModel(BaseModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="UUID")

    class Meta:
        abstract = True
