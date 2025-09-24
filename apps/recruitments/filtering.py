from django.db import models
from rest_framework.request import Request

from apps.recruitments.models import Recruitment


class CustomRecruitmentFilter:
    def __init__(self, request: Request, queryset: models.QuerySet[Recruitment]):
        self.request = request
        self.queryset = queryset

    def filter_queryset(self) -> models.QuerySet[Recruitment]:
        """요청 파라미터를 기반으로 쿼리셋에 모든 필터를 순차적으로 적용합니다."""
        self.queryset = self._filter_by_status()
        self.queryset = self._filter_by_tags()
        self.queryset = self._apply_search()
        self.queryset = self._apply_ordering()
        return self.queryset

    def _filter_by_status(self) -> models.QuerySet[Recruitment]:
        status_param = self.request.query_params.get("status")
        if status_param == "recruiting":
            return self.queryset.filter(is_closed=False)
        if status_param == "closed":
            return self.queryset.filter(is_closed=True)
        return self.queryset

    def _filter_by_tags(self) -> models.QuerySet[Recruitment]:
        tags_param = self.request.query_params.get("tags")
        if tags_param:
            tag_ids = [int(tag_id) for tag_id in tags_param.split(",") if tag_id.isdigit()]
            if tag_ids:
                return self.queryset.filter(tags__id__in=tag_ids).distinct()
        return self.queryset

    def _apply_search(self) -> models.QuerySet[Recruitment]:
        search_param = self.request.query_params.get("search")
        if search_param:
            return self.queryset.filter(title__icontains=search_param)
        return self.queryset

    def _apply_ordering(self) -> models.QuerySet[Recruitment]:
        ordering_param = self.request.query_params.get("ordering", "-created_at")
        valid_ordering_fields = [
            "created_at",
            "-created_at",
            "views_count",
            "-views_count",
            "bookmark_count",
            "-bookmark_count",
        ]
        if ordering_param in valid_ordering_fields:
            return self.queryset.order_by(ordering_param)
        return self.queryset
