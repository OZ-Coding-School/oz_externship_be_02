from django.db import models

from apps.core.models.base import UUIDBaseModel
from apps.lectures.models.categories import Category


class DifficultyChoices(models.TextChoices):
    EASY = "easy", "쉬움"
    NORMAL = "normal", "보통"
    HARD = "hard", "어려움"


class PlatformChoices(models.TextChoices):
    UDEMY = "udemy", "유데미"
    INFLEARN = "inflearn", "인프런"


class Lecture(UUIDBaseModel):
    title = models.CharField(max_length=255, null=False, blank=False)
    instructor = models.CharField(max_length=20, null=False, blank=False)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    duration = models.SmallIntegerField()
    difficulty = models.CharField(max_length=10, choices=DifficultyChoices.choices, default=DifficultyChoices.NORMAL)
    description = models.TextField()
    platform = models.CharField(max_length=10, choices=PlatformChoices.choices)
    original_price = models.BigIntegerField(default=0)
    discount_price = models.BigIntegerField(default=0)
    url_link = models.URLField(max_length=500)
    thumbnail_img_url = models.URLField(max_length=500, null=True, blank=True)

    categories = models.ManyToManyField(
        Category,  # 카텍올이 몯엘과 다대다
        through="lectures.LectureCategory",  # 얘를 통해 ㅎㅎ
        related_name="lectures",
    )

    class Meta:
        db_table = "crawled_lectures"
        unique_together = ["platform", "title"]  # 잉뎅싱

    def __str__(self) -> str:
        return self.title
