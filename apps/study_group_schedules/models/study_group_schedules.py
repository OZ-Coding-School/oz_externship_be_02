from django.db import models

from apps.core.models import BaseModel
from apps.studies.models.group_members import GroupMember
from apps.studies.models.study_groups import StudyGroup
from apps.study_group_schedules.managers import StudyGroupScheduleManager


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

    # Manager 추가
    objects = models.Manager()  # 기본 manager
    schedules = StudyGroupScheduleManager()  # 커스텀 manager

    class Meta:
        db_table = "group_schedules"
        indexes = [
            # 스터디 그룹별 스케줄 조회
            models.Index(fields=["study_group", "session_date"]),
            # 날짜 기반 필터링 및 정렬
            models.Index(fields=["session_date"]),
            # 스터디 그룹별 날짜순 정렬된 스케줄 목록 조회
            models.Index(fields=["study_group", "session_date", "start_time"]),
            # 생성일 기준 정렬
            models.Index(fields=["-created_at"]),
            # 복합 조건: 스터디 그룹 + 날짜 범위 필터링
            models.Index(fields=["study_group", "session_date", "-created_at"]),
        ]
