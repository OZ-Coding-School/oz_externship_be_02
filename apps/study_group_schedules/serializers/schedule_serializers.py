from typing import Any, Dict

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from apps.study_group_schedules.models import GroupSchedule


class StudyGroupScheduleCreateSerializer(serializers.ModelSerializer[GroupSchedule]):
    class Meta:
        model = GroupSchedule
        fields = ["study_group", "title", "objective", "session_date", "start_time", "end_time"]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("시작 시간은 종료 시간보다 이전이어야 합니다.")

        return attrs


class StudyGroupScheduleResponseSerializer(serializers.ModelSerializer[GroupSchedule]):
    study_group_name = serializers.CharField(source="study_group.name", read_only=True)

    class Meta:
        model = GroupSchedule
        fields = [
            "id",
            "study_group",
            "study_group_name",
            "title",
            "objective",
            "session_date",
            "start_time",
            "end_time",
            "created_at",
            "updated_at",
        ]
