from django.db import models

from apps.core.models import BaseModel
from apps.studies.models.study_groups import StudyGroup
from apps.users.models.user import User


class StudyReview(BaseModel):
    """
    스터디 리뷰를 저장하는 테이블
    """

    class RatingEnum(models.IntegerChoices):
        FIVE_STARS = 5
        FOUR_STARS = 4
        THREE_STARS = 3
        TWO_STARS = 2
        ONE_STAR = 1

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name="reviews")
    star_rating = models.IntegerField(choices=RatingEnum.choices, verbose_name="평점")
    content = models.CharField(max_length=500, verbose_name="리뷰 내용")

    class Meta:
        db_table = "reviews"
        unique_together = ("user", "study_group")
