from django.db import models

from apps.core.models import BaseModel
from apps.lectures.models.crawled_lectures import Lecture
from apps.studies.models import StudyGroup


class StudyLecture(BaseModel):
    """
    스터디 그룹에서 듣는 강의들을 저장하는 테이블
    - 강의 id(FK) / 스터디 그룹 id(FK)
    - BaseModel : 생성일자 / 수정일자
    """

    pk = models.CompositePrimaryKey("study_group_id", "lecture_id")
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE)  # 클래스명 확인 필요.
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)

    class Meta:
        db_table = "study_lectures"
