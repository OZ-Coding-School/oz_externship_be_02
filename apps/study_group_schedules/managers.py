from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import Count

if TYPE_CHECKING:
    from apps.study_group_schedules.models import GroupSchedule


class StudyGroupScheduleQuerySet(models.QuerySet["GroupSchedule"]):
    """스터디 그룹 스케줄 커스텀 QuerySet"""

    def filter_by_study_group(self, study_group_id: int) -> StudyGroupScheduleQuerySet:
        """특정 스터디 그룹의 스케줄만 필터링"""
        return self.filter(study_group_id=study_group_id)

    def filter_by_date_range(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> StudyGroupScheduleQuerySet:
        """날짜 범위로 필터링"""
        queryset = self
        if start_date:
            queryset = queryset.filter(session_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(session_date__lte=end_date)
        return queryset

    def filter_upcoming(self) -> StudyGroupScheduleQuerySet:
        """오늘 이후의 스케줄만 필터링"""
        return self.filter(session_date__gte=date.today())

    def filter_past(self) -> StudyGroupScheduleQuerySet:
        """과거 스케줄만 필터링"""
        return self.filter(session_date__lt=date.today())

    def filter_today(self) -> StudyGroupScheduleQuerySet:
        """오늘 스케줄만 필터링"""
        today = date.today()
        return self.filter(session_date=today)

    def order_by_date_asc(self) -> StudyGroupScheduleQuerySet:
        """날짜순 정렬 (오래된 것부터)"""
        return self.order_by("session_date", "start_time")

    def order_by_date_desc(self) -> StudyGroupScheduleQuerySet:
        """날짜 역순 정렬 (최신 것부터)"""
        return self.order_by("-session_date", "-start_time")

    def order_by_created_desc(self) -> StudyGroupScheduleQuerySet:
        """생성일 역순 정렬"""
        return self.order_by("-created_at")

    def with_study_group_info(self) -> StudyGroupScheduleQuerySet:
        """스터디 그룹 정보 포함하여 최적화된 쿼리"""
        return self.select_related("study_group")

    def with_participant_count(self) -> StudyGroupScheduleQuerySet:
        """참여자 수 포함"""
        return self.annotate(participant_count=Count("participants", distinct=True))

    def optimized_for_list(self) -> StudyGroupScheduleQuerySet:
        """목록 조회용 최적화된 쿼리셋"""
        return self.select_related("study_group").annotate(participant_count=Count("participants", distinct=True))

    def filter_by_user_access(self, user_id: int) -> StudyGroupScheduleQuerySet:
        """사용자가 접근 가능한 스케줄만 필터링 (스터디 그룹 멤버인 경우)"""
        return self.filter(study_group__members__id=user_id)


_StudyGroupScheduleManager = models.Manager.from_queryset(StudyGroupScheduleQuerySet)

if TYPE_CHECKING:

    class StudyGroupScheduleManager(_StudyGroupScheduleManager["GroupSchedule"]):
        pass

else:
    StudyGroupScheduleManager = _StudyGroupScheduleManager
