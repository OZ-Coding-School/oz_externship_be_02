from django.db import models

from apps.core.models import BaseModel
from apps.studies.models import GroupMember
from apps.study_group_schedules.models.study_group_schedules import GroupSchedule


class ScheduleParticipant(BaseModel):
    pk = models.CompositePrimaryKey("schedule_id", "member_id")
    schedule = models.ForeignKey(
        GroupSchedule, on_delete=models.CASCADE
    )  # 스터디 그룹 일정 식별자 / 스터디 일정에 대한 테이블 참조
    member = models.ForeignKey(
        GroupMember, on_delete=models.CASCADE
    )  # 스터디 그룹 멤버 식별자 / 스터디 그룹 멤버에 대한 테이블 참조

    class Meta:
        db_table = "schedule_participants"
