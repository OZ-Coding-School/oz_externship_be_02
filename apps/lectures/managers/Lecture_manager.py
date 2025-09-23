from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from django.db import models
from django.db.models import Q

if TYPE_CHECKING:
    from apps.lectures.models.crawled_lectures import Lecture


class LectureQuerySet(models.QuerySet["Lecture"]):
    def search(self, keyword: str) -> LectureQuerySet:
        if not keyword:
            return self
        return self.filter(Q(title__icontains=keyword) | Q(instructor__icontains=keyword))

    def filter_by_categories(self, category_names: Optional[str]) -> LectureQuerySet:
        if not category_names:
            return self
        names = [name.strip() for name in category_names.split(",")]
        return self.filter(categories__name__in=names).distinct()

    def sort_by_ordering(self, ordering: str) -> LectureQuerySet:
        order_map = {
            "price_asc": "original_price",
            "price_desc": "-original_price",
            "rating_asc": "average_rating",
            "rating_desc": "-average_rating",
            "oldest": "updated_at",
        }
        order_by_field = order_map.get(ordering, "-updated_at")
        return self.order_by(order_by_field)


class LectureManager(models.Manager["Lecture"]):
    def get_queryset(self) -> LectureQuerySet:
        return LectureQuerySet(self.model, using=self._db)

    def search(self, keyword: str) -> LectureQuerySet:
        return self.get_queryset().search(keyword)

    def filter_by_categories(self, category_names: Optional[str]) -> LectureQuerySet:
        return self.get_queryset().filter_by_categories(category_names)
