import uuid

from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, help_text="생성일시")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, help_text="수정 일시")

    class Meta:
        abstract = True


class UUIDBaseModel(BaseModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, help_text="UUID")

    class Meta:
        abstract = True
