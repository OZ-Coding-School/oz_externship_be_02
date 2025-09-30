from __future__ import annotations

from datetime import date, time, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from django.db.models import Q, QuerySet

from apps.study_group_schedules.enums import ScheduleOrdering
from apps.users.models import User

if TYPE_CHECKING:
    from apps.study_group_schedules.models import GroupSchedule
else:
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

    # 기본 쿼리셋: 사용자가 접근 가능한 스케줄만
    queryset = GroupSchedule.schedules.filter_by_user_access(user_id).with_study_group_info()

    # 특정 스터디 그룹 필터링
    if study_group_uuid:
        if isinstance(study_group_uuid, str):
            study_group_uuid = UUID(study_group_uuid)
        queryset = queryset.filter(study_group__uuid=study_group_uuid)

    # 날짜 범위 필터링
    if start_date or end_date:
        queryset = queryset.filter_by_date_range(start_date=start_date, end_date=end_date)

    # 정렬
    if ordering == ScheduleOrdering.DATE_ASC:
        queryset = queryset.order_by_date_asc()
    else:
        # 기본값: 날짜 역순 (DATE_DESC 포함)
        queryset = queryset.order_by_date_desc()

    return queryset


def get_upcoming_schedules_for_user(user_id: int, days_ahead: int = 3) -> QuerySet["GroupSchedule"]:
    """사용자의 다가오는 스케줄 목록 조회 (기본 3일 이내)"""
    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    return (
        GroupSchedule.schedules.filter_by_user_access(user_id)
        .filter_by_date_range(start_date=today, end_date=end_date)
        .with_study_group_info()
        .order_by_date_asc()
    )


def get_today_schedules_for_user(user_id: int) -> QuerySet["GroupSchedule"]:
    """사용자의 오늘 스케줄 목록 조회"""
    return (
        GroupSchedule.schedules.filter_by_user_access(user_id)
        .filter_today()
        .with_study_group_info()
        .order_by(ScheduleOrdering.TIME_ASC)
    )


def get_study_group_upcoming_schedules(study_group_uuid: UUID, days_ahead: int = 3) -> QuerySet["GroupSchedule"]:
    """특정 스터디 그룹의 다가오는 스케줄 목록 조회 (기본 3일 이내)"""
    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    return (
        GroupSchedule.schedules.filter_by_study_group(study_group_uuid)
        .filter_by_date_range(start_date=today, end_date=end_date)
        .with_study_group_info()
        .order_by_date_asc()
    )


def get_schedule_by_id_for_user(
    schedule_id: int,
    user_id: int,
    study_group_uuid: str | UUID | None = None,
    include_detailed_info: bool = False,
) -> GroupSchedule | None:
    """
    사용자가 접근 가능한 특정 스케줄을 조회하는 서비스 함수

    Args:
        schedule_id: 스케줄 ID
        user_id: 사용자 ID
        study_group_uuid: 스터디 그룹 UUID
        include_detailed_info: 상세 정보 포함 여부

    Returns:
        GroupSchedule 객체 또는 None (접근 권한이 없거나 존재하지 않는 경우)
    """
    try:
        # 기본 쿼리: 사용자가 접근 가능한 스케줄만
        queryset = GroupSchedule.schedules.filter_by_user_access(user_id).filter(id=schedule_id).with_study_group_info()

        # 특정 스터디 그룹 UUID가 제공된 경우 추가 필터링
        if study_group_uuid:
            if isinstance(study_group_uuid, str):
                study_group_uuid = UUID(study_group_uuid)
            queryset = queryset.filter(study_group__uuid=study_group_uuid)

        # 상세 정보 포함 여부에 따른 쿼리 최적화
        if include_detailed_info:
            queryset = queryset.get_with_detailed_info()
        else:
            queryset = queryset.with_study_group_info()

        return queryset.first()

    except ValueError:
        return None


def get_schedule_for_update(schedule_id: int, user_id: int, study_group_uuid: str | UUID) -> GroupSchedule | None:
    """수정을 위한 스케줄 조회"""
    try:
        return GroupSchedule.schedules.get_for_update(
            schedule_id=schedule_id, user_id=user_id, study_group_uuid=study_group_uuid
        ).first()
    except (ValueError, GroupSchedule.DoesNotExist):
        return None


def validate_user_can_edit_schedule(user: User, schedule: GroupSchedule) -> bool:
    """사용자가 스케줄을 수정할 수 있는지 확인"""
    from apps.studies.models import GroupMember

    # 스터디 그룹 리더만 수정 가능
    is_leader = GroupMember.objects.filter(study_group=schedule.study_group, user=user, is_leader=True).exists()

    return is_leader


def can_user_edit_schedule(user_id: int, schedule_id: int, study_group_uuid: str | UUID) -> bool:
    """사용자가 특정 스케줄을 수정할 수 있는지 간단 확인"""
    try:
        # 스케줄이 존재하고 사용자가 접근 가능한지 확인
        schedule_exists = (
            GroupSchedule.schedules.filter(id=schedule_id, study_group__uuid=study_group_uuid)
            .filter_by_user_access(user_id)
            .exists()
        )

        if not schedule_exists:
            return False

        # 수정 권한이 있는지 확인 (스터디 그룹의 멤버)
        can_edit = (
            GroupSchedule.schedules.filter(id=schedule_id, study_group__uuid=study_group_uuid)
            .filter(study_group__members=user_id)
            .exists()
        )

        return can_edit

    except (ValueError, Exception):
        return False


def get_editable_schedules_for_user(user_id: int, study_group_uuid: str | UUID | None = None) -> list[GroupSchedule]:
    """사용자가 수정 가능한 스케줄 목록 조회"""
    queryset = GroupSchedule.schedules.filter_editable_by_user(user_id)

    if study_group_uuid:
        if isinstance(study_group_uuid, str):
            study_group_uuid = UUID(study_group_uuid)
        queryset = queryset.filter(study_group__uuid=study_group_uuid)

    return list(queryset.with_study_group_info().order_by("-session_date"))


def check_schedule_edit_conflicts(
    schedule: GroupSchedule,
    new_session_date: date | None = None,
    new_start_time: time | None = None,
    new_end_time: time | None = None,
) -> dict[str, str] | None:
    """스케줄 수정 시 충돌 확인"""
    from datetime import datetime

    # 변경될 값들 결정
    session_date = new_session_date or schedule.session_date
    start_time = new_start_time or schedule.start_time
    end_time = new_end_time or schedule.end_time

    # 같은 스터디 그룹의 다른 스케줄과 시간 충돌 확인
    conflicting_schedules = GroupSchedule.objects.filter(
        study_group=schedule.study_group, session_date=session_date
    ).exclude(id=schedule.id)

    for other_schedule in conflicting_schedules:
        # 시간 겹침 확인
        if start_time < other_schedule.end_time and end_time > other_schedule.start_time:
            return {
                "conflict_type": "time_overlap",
                "conflict_schedule_id": str(other_schedule.id),
                "conflict_schedule_title": other_schedule.title,
                "message": f'같은 날짜에 다른 스케줄 "{other_schedule.title}"과 시간이 겹칩니다.',
            }

    return None
