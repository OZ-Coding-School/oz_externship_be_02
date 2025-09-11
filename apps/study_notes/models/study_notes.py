from django.db import models

from apps.core.models import BaseModel
from apps.studies.models.study_groups import StudyGroup
from apps.study_notes.managers import StudyNoteManager
from apps.users.models.user import User


class StudyNote(BaseModel):
    """
    스터디 노트 기록을 저장하는 테이블
    """

    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name="study_notes")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="study_notes")
    title = models.CharField(max_length=50)
    content = models.TextField()
    ai_summary = models.TextField()

    objects = StudyNoteManager()

    class Meta:
        db_table = "study_notes"


class StudyNoteImage(BaseModel):
    """
    스터디 노트 기록에 들어가는 이미지를 저장하는 테이블
    """

    study_note = models.ForeignKey(StudyNote, on_delete=models.CASCADE, related_name="images")
    img_url = models.URLField(max_length=255)

    class Meta:
        db_table = "study_note_images"


class StudyNoteAttachment(BaseModel):
    """
    스터디 노트 기록에 들어가는 파일을 저장하는 테이블
    """

    study_note = models.ForeignKey(StudyNote, on_delete=models.CASCADE, related_name="attachments")
    file_url = models.URLField(max_length=255)
    file_name = models.CharField(max_length=50)

    class Meta:
        db_table = "study_note_attachments"
