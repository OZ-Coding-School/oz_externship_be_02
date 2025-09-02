from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models.base import UUIDBaseModel
from apps.lectures.models.crawled_lectures import Lecture
from apps.users.models.user import User


class StudyGroup(UUIDBaseModel):
    """
    생성된 스터디 그룹를 저장하는 테이블
    - id / 스터디그룹명 / 스터디그룹 소개 / 최대인원 / 스터디그룹 이미지 / 시작일 / 종료일 / 스터디 진행 상황
    - UUIDBaseModel : uuid
    - BaseModel : 생성일자 / 수정일자
    """

    class StatusChoices(models.TextChoices):
        """
        status에 들어가는 Enum 정의. 장고의 'choices' 구조로 정의
        튜플로 정의됨.
        """

        PENDING = "PENDING", "대기중"
        ONGOING = "ONGOING", "진행중"
        ENDED = "ENDED", "종료됨"

    name = models.CharField(max_length=20)
    introduction = models.CharField(max_length=500, null=True)
    max_headcount = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    profile_img_url = models.URLField(max_length=255, null=True, blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=StatusChoices.choices, default=StatusChoices.PENDING)

    # 테이블 관계성
    lectures = models.ManyToManyField(  # 강의 목록, 다대다 테이블
        Lecture,  # 클래스명 확인 필요
        through="studies.StudyLecture",  # 중간 테이블 지정
    )
    members = models.ManyToManyField(  # 스터디 멤버, 다대다 테이블
        User,  # 클래스명 확인 필요.
        through="studies.GroupMember",  # 중간 테이블 지정
    )

    class Meta:
        db_table = "study_groups"
