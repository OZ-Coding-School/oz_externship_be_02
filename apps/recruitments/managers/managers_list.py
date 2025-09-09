from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast

from django.db import models
from django.db.models import Count, OuterRef, Subquery

# 순환참조를 하지 않고 범용성을 위해 _T 사용
if TYPE_CHECKING:
    from apps.recruitments.models import Recruitment
_T = TypeVar("_T", bound="Recruitment")


class RecruitmentListQuerySet(models.QuerySet[_T]):
    def filter_is_closed(self) -> RecruitmentListQuerySet[_T]:
        return self.filter(is_closed=False)

    def order_last(self) -> RecruitmentListQuerySet[_T]:
        return self.order_by("-created_at")

    def optimized_queryset(self) -> RecruitmentListQuerySet[_T]:
        # 순환참조를 피하기 위해서 메소드 안에서 임포트
        from apps.recruitments.models.recruitment_images import RecruitmentImage

        # 시리얼라이저에 필요한 정보 채우기
        # outerref : https://www.reddit.com/r/django/comments/q40km4/help_understanding_outerref/?tl=ko
        img_subquery = RecruitmentImage.objects.filter(recruitment=OuterRef("id")).values("img_url")[:1]
        optimized_queryset = (
            self.annotate(img=Subquery(img_subquery), bookmarks_count=Count("bookmark_users", distinct=True))
            .select_related("study_group")
            .prefetch_related("study_group__lectures", "tags")
        )
        return cast(RecruitmentListQuerySet[_T], optimized_queryset)


# Mypy가 분석할 때 동적할당은 안잡아서 변수에 할당해서 정적클래스로 검사하고 동적으로 사용함
_RecruitmentListManager = models.Manager.from_queryset(RecruitmentListQuerySet)
if TYPE_CHECKING:

    class RecruitmentListManager(_RecruitmentListManager[_T]):
        pass

else:
    RecruitmentListManager = _RecruitmentListManager
