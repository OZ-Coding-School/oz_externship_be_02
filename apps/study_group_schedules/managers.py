from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from django.db import models
from django.db.models import Count

from apps.study_group_schedules.enums import ScheduleOrdering

if TYPE_CHECKING:
    from apps.study_group_schedules.models import GroupSchedule


class StudyGroupScheduleQuerySet(models.QuerySet["GroupSchedule"]):
    """스터디 그룹 스케줄 커스텀 QuerySet"""

    def filter_by_study_group(self, study_group_id: int) -> "StudyGroupScheduleQuerySet":
        """특정 스터디 그룹의 스케줄만 필터링"""
        return self.filter(study_group_id=study_group_id)

    def filter_by_date_range(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> "StudyGroupScheduleQuerySet":
        """날짜 범위로 필터링"""
        queryset = self
        if start_date:
            queryset = queryset.filter(session_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(session_date__lte=end_date)
        return queryset

    def filter_upcoming(self) -> "StudyGroupScheduleQuerySet":
        """오늘 이후의 스케줄만 필터링"""
        return self.filter(session_date__gte=date.today())

    def filter_past(self) -> "StudyGroupScheduleQuerySet":
        """과거 스케줄만 필터링"""
        return self.filter(session_date__lt=date.today())

    def filter_today(self) -> "StudyGroupScheduleQuerySet":
        """오늘 스케줄만 필터링"""
        return self.filter(session_date=date.today())

    def order_by_date_asc(self) -> "StudyGroupScheduleQuerySet":
        """날짜순 정렬 (오래된 것부터)"""
        return self.order_by(ScheduleOrdering.DATE_ASC, ScheduleOrdering.TIME_ASC)

    def order_by_date_desc(self) -> "StudyGroupScheduleQuerySet":
        """날짜 역순 정렬 (최신 것부터)"""
        return self.order_by(ScheduleOrdering.DATE_DESC, ScheduleOrdering.TIME_DESC)

    def order_by_created_desc(self) -> "StudyGroupScheduleQuerySet":
        """생성일 역순 정렬"""
        return self.order_by(ScheduleOrdering.CREATED_DESC)

    def with_study_group_info(self) -> "StudyGroupScheduleQuerySet":
        """스터디 그룹 정보 포함하여 최적화된 쿼리"""
        return self.select_related("study_group")

    def with_participant_count(self) -> "StudyGroupScheduleQuerySet":
        """참여자 수 포함"""
        return self.annotate(participant_count=Count("participants", distinct=True))

    def optimized_for_list(self) -> "StudyGroupScheduleQuerySet":
        """목록 조회용 쿼리셋"""
        return self.with_study_group_info().with_participant_count()

    def filter_by_user_access(self, user_id: int) -> "StudyGroupScheduleQuerySet":
        """사용자가 접근 가능한 스케줄만 필터링"""
        return self.filter(study_group__members__id=user_id)

    def get_schedule_for_user_detail(self, schedule_id: int, user_id: int) -> "StudyGroupScheduleQuerySet":
        """상세조회용 스케줄 쿼리셋"""
        return (
            self.filter(id=schedule_id)
            .filter_by_user_access(user_id)
            .select_related("study_group")
            .prefetch_related("participants", "participants__user")
            .with_participant_count()
        )

    def get_with_detailed_info(self) -> "StudyGroupScheduleQuerySet":
        """상세 정보를 포함한 스케줄 조회용 쿼리셋"""
        return (
            self.select_related("study_group")
            .prefetch_related("participants", "participants__user")
            .with_participant_count()
        )

    def filter_accessible_by_user_and_group(
        self, user_id: int, study_group_uuid: str | UUID
    ) -> "StudyGroupScheduleQuerySet":
        """
        특정 사용자가 특정 스터디 그룹에서 접근 가능한 스케줄만 필터링

        Args:
            user_id: 사용자 ID
            study_group_uuid: 스터디 그룹 UUID

        Returns:
            필터링된 QuerySet
        """
        return self.filter(study_group__members__id=user_id, study_group__uuid=study_group_uuid)


StudyGroupScheduleManager = models.Manager.from_queryset(StudyGroupScheduleQuerySet)
