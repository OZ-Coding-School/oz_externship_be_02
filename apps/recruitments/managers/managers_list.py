from __future__ import annotations

from typing import TYPE_CHECKING, Self, cast

from django.apps import apps
from django.db import models
from django.db.models import Count, OuterRef, Subquery

# 순환참조를 하지 않고 범용성을 위해 _T 사용
if TYPE_CHECKING:   # pragma: no cover
    from apps.recruitments.models import Recruitment
    from apps.recruitments.models.recruitment_images import RecruitmentImage
    from apps.users.models import User


class RecruitmentListQuerySet(models.QuerySet["Recruitment"]):
    def filter_is_closed(self) -> Self:
        return self.filter(is_closed=False)

    def sort_by_latest(self) -> Self:
        return self.order_by("-created_at")

    def recm_list_queryset(self) -> Self:
        # 순환참조를 피하기 위해서 'images'라는 역방향 관계 필드를 이용해 모델 class 이용
        reverse_relation = self.model._meta.get_field("images")
        RecruitmentImage = cast("RecruitmentImage", reverse_relation.related_model)

        # 시리얼라이저에 필요한 정보 채우기
        # outerref : https://www.reddit.com/r/django/comments/q40km4/help_understanding_outerref/?tl=ko
        img_subquery = RecruitmentImage.objects.filter(recruitment=OuterRef("id")).values("img_url")[:1]
        optimized_queryset = (
            self.annotate(img=Subquery(img_subquery), bookmarks_count=Count("bookmark_users", distinct=True))
            .select_related("study_group")
            .prefetch_related("study_group__lectures", "tags")
        )
        return optimized_queryset

    def get_bookmarked_recruitments(self, user: "User") -> Self:
        """특정 사용자가 북마크한 공고 목록을 반환합니다."""
        return self.filter(bookmark_users=user).recm_list_queryset()

# Mypy가 분석할 때 동적할당은 안잡아서 변수에 할당해서 정적클래스로 검사하고 동적으로 사용함
_RecruitmentListManager = models.Manager.from_queryset(RecruitmentListQuerySet)
if TYPE_CHECKING:   # pragma: no cover

    class RecruitmentListManager(_RecruitmentListManager["Recruitment"]):
        pass

else:
    RecruitmentListManager = _RecruitmentListManager


class AdminRecruitmentQuerySet(models.QuerySet["Recruitment"]):
    def with_counts(self) -> Self:
        return self.annotate(bookmark_count=Count("bookmark_users", distinct=True))

    def prefetch_tags(self) -> Self:
        return self.prefetch_related("tags")


class AdminRecruitmentManager(models.Manager["Recruitment"]):
    def get_queryset(self) -> AdminRecruitmentQuerySet:
        return AdminRecruitmentQuerySet(self.model, using=self._db)

    def get_admin_listings(self) -> AdminRecruitmentQuerySet:
        return self.get_queryset().with_counts().prefetch_tags()
