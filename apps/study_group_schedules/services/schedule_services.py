from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from django.db.models import QuerySet

from apps.study_group_schedules.enums import ScheduleOrdering
from apps.study_group_schedules.models import GroupSchedule

if TYPE_CHECKING:
    from apps.study_group_schedules.models import GroupSchedule


def get_user_accessible_schedules(
    user_id: int,
    study_group_uuid: str | UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    ordering: str = ScheduleOrdering.DATE_DESC,
) -> QuerySet["GroupSchedule"]:
    """
    사용자가 접근 가능한 스케줄 목록을 가져오는 서비스 함수

    Args:
        user_id: 사용자 ID
        study_group_uuid: 스터디 그룹 UUID (선택)
        start_date: 시작 날짜 (선택)
        end_date: 종료 날짜 (선택)
        ordering: 정렬 방식

    Returns:
        최적화된 스케줄 QuerySet
    """

    # 기본 쿼리셋: 사용자가 속한 스터디 그룹의 스케줄만
    queryset = GroupSchedule.objects.select_related("study_group").filter(study_group__members__id=user_id)

    # 특정 스터디 그룹 필터링
    if study_group_uuid:
        if isinstance(study_group_uuid, str):
            study_group_uuid = UUID(study_group_uuid)
        queryset = queryset.filter(study_group__uuid=study_group_uuid)

    # 날짜 범위 필터링
    if start_date:
        queryset = queryset.filter(session_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(session_date__lte=end_date)

    # 정렬
    if ordering == ScheduleOrdering.DATE_ASC:
        queryset = queryset.order_by(ScheduleOrdering.DATE_ASC, ScheduleOrdering.TIME_ASC)
    else:
        # 기본값: 날짜 역순 (DATE_DESC 포함)
        queryset = queryset.order_by(ScheduleOrdering.DATE_DESC, ScheduleOrdering.TIME_DESC)

    return queryset


def get_upcoming_schedules_for_user(user_id: int, days_ahead: int = 3) -> QuerySet["GroupSchedule"]:
    """사용자의 다가오는 스케줄 목록 조회 (기본 3일 이내)"""
    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    return (
        GroupSchedule.objects.select_related("study_group")
        .filter(study_group__members__id=user_id, session_date__gte=today, session_date__lte=end_date)
        .order_by(ScheduleOrdering.DATE_ASC, ScheduleOrdering.TIME_ASC)
    )


def get_today_schedules_for_user(user_id: int) -> QuerySet["GroupSchedule"]:
    """사용자의 오늘 스케줄 목록 조회"""

    return (
        GroupSchedule.objects.select_related("study_group")
        .filter(study_group__members__id=user_id, session_date=date.today())
        .order_by(ScheduleOrdering.TIME_ASC)
    )


def get_study_group_upcoming_schedules(study_group_id: int, days_ahead: int = 3) -> QuerySet["GroupSchedule"]:
    """특정 스터디 그룹의 다가오는 스케줄 목록 조회 (기본 3일 이내)"""
    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    return (
        GroupSchedule.objects.select_related("study_group")
        .filter(study_group_id=study_group_id, session_date__gte=today, session_date__lte=end_date)
        .order_by(ScheduleOrdering.DATE_ASC, ScheduleOrdering.TIME_ASC)
    )
