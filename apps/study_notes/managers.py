# apps/study_notes/managers.py
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from apps.studies.models import StudyGroup
from apps.users.models import User

if TYPE_CHECKING:
    from apps.study_notes.models.study_notes import StudyNote


class StudyNoteManager(models.Manager["StudyNote"]):
    def create_note(
        self,
        author: User,
        study_group: StudyGroup,
        title: str,
        content: str,
    ) -> StudyNote:
        """
        스터디 노트를 생성하는 메서드
        """
        note = self.create(
            author=author,
            study_group=study_group,
            title=title,
            content=content,
            ai_summary="AI 요약은 추후 자동 생성됩니다.",
        )
        return note
