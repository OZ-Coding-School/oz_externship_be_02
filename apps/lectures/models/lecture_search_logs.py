from django.db import models

from apps.core.models import BaseModel
from apps.users.models.user import User


class LectureSearchLog(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name="search_logs")
    keyword = models.CharField(max_length=255, null=False)

    class Meta:
        db_table = "lecture_search_logs"
