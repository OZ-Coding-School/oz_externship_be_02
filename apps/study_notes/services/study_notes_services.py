from typing import Optional

from django.core.files.uploadedfile import UploadedFile

from apps.core.utils.s3_uploader import S3Uploader
from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import (
    StudyNote,
    StudyNoteAttachment,
    StudyNoteImage,
)
from apps.users.models.user import User


class StudyNoteService:
    def __init__(self, s3_uploader: Optional[S3Uploader] = None) -> None:
        self.s3 = s3_uploader or S3Uploader()

    def create_study_note(
        self,
        author: User,
        study_group: StudyGroup,
        title: str,
        content: str,
        images: Optional[list[UploadedFile]] = None,
        attachments: Optional[list[UploadedFile]] = None,
    ) -> StudyNote:

        note = StudyNote.objects.create_note(
            author=author,
            study_group=study_group,
            title=title,
            content=content,
        )

        # 이미지 업로드
        if images:
            image_objs = []
            for img_file in images:
                s3_data = self.s3.upload_file(img_file)
                image_objs.append(StudyNoteImage(study_note=note, img_url=s3_data["url"]))
            StudyNoteImage.objects.bulk_create(image_objs)

        # 첨부파일 업로드
        if attachments:
            attachment_objs = []
            for attach_file in attachments:
                s3_data = self.s3.upload_file(attach_file)
                attachment_objs.append(
                    StudyNoteAttachment(
                        study_note=note,
                        file_name=attach_file.name or "untitled",
                        file_url=s3_data["url"],
                    )
                )
            StudyNoteAttachment.objects.bulk_create(attachment_objs)

        return note
