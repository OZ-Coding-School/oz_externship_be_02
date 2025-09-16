from django.db import models

from apps.core.models import BaseModel
from apps.lectures.models.crawled_lectures import Lecture


class RatingChoices(models.TextChoices):
    FIVE_STARS = "5_OUT_OF_5_STARS", "별점 5점"
    FOUR_STARS = "4_OUT_OF_5_STARS", "별점 4점"
    THREE_STARS = "3_OUT_OF_5_STARS", "별점 3점"
    TWO_STARS = "2_OUT_OF_5_STARS", "별점 2점"
    ONE_STAR = "1_OUT_OF_5_STARS", "별점 1점"


class LectureReview(BaseModel):
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,  # 동반 자살
        related_name="reviews",  # 역참조 시 사용
        null=False,
    )
    rating = models.CharField(max_length=20, choices=RatingChoices.choices, null=False, blank=False)
    content = models.TextField(blank=True)

    class Meta:
        db_table = "crawled_lecture_reviews"

    def __str__(self) -> str:
        return f"{self.lecture.title} 리뷰"
