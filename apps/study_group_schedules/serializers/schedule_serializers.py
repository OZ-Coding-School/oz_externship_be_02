from datetime import date, datetime, time, timedelta
from typing import Any, Dict

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from apps.studies.models.study_groups import StudyGroup
from apps.study_group_schedules.models import GroupSchedule


class StudyGroupScheduleResponseSerializer(serializers.ModelSerializer[GroupSchedule]):

    study_group_uuid = serializers.UUIDField(source="study_group.uuid", read_only=True)
    study_group_name = serializers.CharField(source="study_group.name", read_only=True)

    class Meta:
        model = GroupSchedule
        fields = [
            "id",
            "title",
            "objective",
            "session_date",
            "start_time",
            "end_time",
            "study_group_uuid",
            "study_group_name",
            "created_at",
            "updated_at",
        ]


# 입력용 시리얼라이저 (30분 검증 포함)
class StudyGroupScheduleCreateSerializer(serializers.ModelSerializer[GroupSchedule]):
    """스터디 그룹 일정 생성 시리얼라이저 - 검증 로직 포함"""

    class Meta:
        model = GroupSchedule
        fields = ["study_group", "title", "objective", "session_date", "start_time", "end_time"]

    def validate_session_date(self, value: date) -> date:
        """날짜 검증: 오늘 이후로만 가능"""
        if value < date.today():
            raise serializers.ValidationError("스케줄 날짜는 오늘 이후로만 설정 가능합니다.")
        return value

    def validate_time_range(self, start_time: time, end_time: time) -> None:
        """시간 검증"""

        # 시작 시간이 종료 시간보다 늦거나 같은 경우
        if start_time >= end_time:
            raise serializers.ValidationError("시작 시간은 종료 시간보다 이전이어야 합니다.")

        # 최소 30분 간격 검증
        base_date = date.today()
        duration = datetime.combine(base_date, end_time) - datetime.combine(base_date, start_time)
        if duration < timedelta(minutes=30):
            raise serializers.ValidationError("스터디 시간은 최소 30분 이상이어야 합니다.")

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """통합 검증"""
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        if start_time and end_time:
            self.validate_time_range(start_time, end_time)

        return data


class StudyGroupScheduleListQueryParamsSerializer(serializers.Serializer[GroupSchedule]):
    """스터디 그룹 스케줄 목록 조회 쿼리 파라미터 시리얼라이저"""

    start_date = serializers.DateField(required=False, help_text="조회 시작 날짜 (YYYY-MM-DD)")
    end_date = serializers.DateField(required=False, help_text="조회 종료 날짜 (YYYY-MM-DD)")
    ordering = serializers.ChoiceField(
        choices=[
            ("session_date", "날짜순"),
            ("-session_date", "날짜 역순"),
        ],
        default="-session_date",
        required=False,
        help_text="정렬 옵션",
    )

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """날짜 범위 검증"""
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError("시작 날짜는 종료 날짜보다 이전이어야 합니다.")

        return data
