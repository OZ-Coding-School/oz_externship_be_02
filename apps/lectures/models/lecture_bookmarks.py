from django.db import models

from apps.core.models import BaseModel
from apps.lectures.models.crawled_lectures import Lecture
from apps.users.models.user import User


class LectureBookmark(BaseModel):
    pk = models.CompositePrimaryKey("user_id", "lecture_id")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, null=False)

    class Meta:
        db_table = "lecture_bookmarks"
