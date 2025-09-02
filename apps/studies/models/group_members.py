from django.db import models

from apps.core.models import BaseModel
from apps.studies.models.study_groups import StudyGroup
from apps.users.models.user import User


class GroupMember(BaseModel):
    """
    스터디 그룹 멤버들의 데이터를 저장하는 테이블
    - id / 스터디 그룹 id(FK) / 유저 id(FK) / 리더여부
    - BaseModel : 생성일자 / 수장일자
    """

    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 클래스명 확인 필요
    is_leader = models.BooleanField(default=False, null=False)

    class Meta:
        db_table = "group_members"
        unique_together = ("study_group_id", "user_id")  # 하나의 스터디 그룹에 특정유저 데이터 중복 방지.
