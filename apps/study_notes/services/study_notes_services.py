from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import (
    StudyNote,
    StudyNoteAttachment,
    StudyNoteImage,
)
from apps.users.models.user import User


class StudyNoteService:
    def create_study_note(
        self, author: User, study_group: StudyGroup, title: str, content: str, images=None, attachments=None
    ) -> StudyNote:
        """
        스터디 노트 생성을 위한 비즈니스 로직을 처리하고, DB에 직접 저장합니다.
        """

        # Django ORM을 사용하여 데이터베이스에 직접 저장합니다.
        note = StudyNote.objects.create(
            author=author,
            study_group=study_group,
            title=title,
            content=content,
            ai_summary="AI 요약은 추후 자동 생성됩니다.",
        )

        # 이미지 저장
        if images:
            for url in images:
                StudyNoteImage.objects.create(study_note=note, img_url=url)

        # 파일 저장
        if attachments:
            for attach in attachments:
                StudyNoteAttachment.objects.create(
                    study_note=note, file_url=attach["file_url"], file_name=attach["file_name"]
                )

        return note
