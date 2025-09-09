from typing import Any, Dict

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from apps.study_group_schedules.models import GroupSchedule


class StudyGroupScheduleResponseSerializerWithUUID(serializers.ModelSerializer[GroupSchedule]):
    """스터디 그룹의 UUID 사용"""

    study_group_name = serializers.CharField(source="study_group.name", read_only=True)
    study_group_uuid = serializers.UUIDField(source="study_group.uuid", read_only=True)  # 스터디 그룹의 UUID

    class Meta:
        model = GroupSchedule
        fields = [
            "id",  # 스케줄 자체의 ID
            "title",
            "objective",
            "session_date",
            "start_time",
            "end_time",
            "study_group",
            "study_group_name",
            "study_group_uuid",  # 스터디 그룹의 UUID
            "created_at",
            "updated_at",
        ]


# 입력용 시리얼라이저 (30분 검증 포함)
class StudyGroupScheduleCreateSerializer(serializers.ModelSerializer[GroupSchedule]):
    """스터디 그룹 일정 생성 시리얼라이저 - 검증 로직 포함"""

    class Meta:
        model = GroupSchedule
        fields = ["study_group", "title", "objective", "session_date", "start_time", "end_time"]

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """종합 검증 로직: 날짜 + 시간"""
        from datetime import date, datetime, timedelta

        session_date = data.get("session_date")
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        # 1. 날짜 검증: 오늘 이후로만 가능
        if session_date:
            today = date.today()
            if session_date < today:
                raise serializers.ValidationError("스케줄 날짜는 오늘 이후로만 설정 가능합니다.")

        # 2. 시간 검증
        if start_time and end_time:
            # 2-1. 시작 시간이 종료 시간보다 늦거나 같은 경우
            if start_time >= end_time:
                raise serializers.ValidationError("시작 시간은 종료 시간보다 이전이어야 합니다.")

            # 2-2. 최소 30분 간격 검증
            start_datetime = datetime.combine(datetime.today(), start_time)
            end_datetime = datetime.combine(datetime.today(), end_time)
            duration = end_datetime - start_datetime

            if duration < timedelta(minutes=30):
                raise serializers.ValidationError("스터디 시간은 최소 30분 이상이어야 합니다.")

        return data
