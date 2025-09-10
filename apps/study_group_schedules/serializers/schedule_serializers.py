from datetime import date, datetime, time, timedelta
from typing import Any, Dict

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from apps.studies.models.study_groups import StudyGroup
from apps.study_group_schedules.models import GroupSchedule


class StudyGroupSerializer(serializers.ModelSerializer[StudyGroup]):
    """스터디 그룹 정보를 위한 Nested Serializer"""

    class Meta:
        model = StudyGroup
        fields = [
            "id",
            "uuid",
            "name",
            "introduction",
            "max_headcount",
            "profile_img_url",
            "start_at",
            "end_at",
            "status",
        ]


class StudyGroupScheduleResponseSerializer(serializers.ModelSerializer[GroupSchedule]):
    """스터디 그룹 Nested Serializer 사용"""

    study_group = StudyGroupSerializer(read_only=True)

    class Meta:
        model = GroupSchedule
        fields = [
            "id",
            "title",
            "objective",
            "session_date",
            "start_time",
            "end_time",
            "study_group",
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
