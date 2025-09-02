from django.db import models

from apps.core.models import BaseModel
from apps.studies.models.group_members import GroupMember
from apps.studies.models.study_groups import StudyGroup


class GroupSchedule(BaseModel):
    study_group = models.ForeignKey(
        StudyGroup, on_delete=models.CASCADE
    )  # 스터디 그룹 식별자 / 스터디 그룹에 대한 테이블 참조
    title = models.CharField(max_length=50)  # 스케줄 이름
    objective = models.CharField(max_length=255)  # 학습 목표 설정 내용
    session_date = models.DateField()  # 스터디 진행일
    start_time = models.TimeField()  # 스터디 시작 시간
    end_time = models.TimeField()  # 스터디 종료 시간

    participants = models.ManyToManyField(GroupMember, through="study_group_schedules.ScheduleParticipant")

    class Meta:
        db_table = "group_schedules"
