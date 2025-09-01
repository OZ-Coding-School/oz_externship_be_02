from django.db import models
from uuid import uuid4
from apps.lectures.models.categories_model import CategoryModel

class DifficultyChoices(models.TextChoices):
    EASY = 'easy', '쉬움'
    NORMAL = 'normal', '보통'
    HARD = 'hard', '어려움'

class PlatformChoices(models.TextChoices):
    UDEMY = 'udemy', '유데미'
    INFLEARN = 'inflearn', '인프런'

class LectureModel(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255, null=False, blank=False)
    instructor = models.CharField(max_length=20, null=False, blank=False)
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00
    )
    duration = models.SmallIntegerField()
    difficulty = models.CharField(
        max_length=10, choices=DifficultyChoices.choices, default=DifficultyChoices.NORMAL
    )
    description = models.TextField()
    platform = models.CharField(
        max_length=10, choices=PlatformChoices.choices
    )
    original_price = models.BigIntegerField(default=0)
    discount_price = models.BigIntegerField(default=0)
    url_link = models.CharField(max_length=255)
    thumbnail_img_url = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    categories = models.ManyToManyField(
        CategoryModel, # 카텍올이 몯엘과 다대다
        through='LectureCategoryModel', # 얘를 통해 ㅎㅎ
        related_name='lectures',
    )
    class Meta:
        db_table = 'crawled_lectures'
        verbose_name = '크롤링 강의'
        verbose_name_plural = '크롤링 강의 목록'
        unique_together = ('platform', 'title')  # 복합히 + 잉뎅싱

    def __str__(self):
        return self.title