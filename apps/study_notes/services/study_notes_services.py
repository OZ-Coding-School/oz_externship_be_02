from typing import List, Optional, Union

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from apps.core.utils.s3_uploader import S3Uploader
from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import (
    StudyNote,
    StudyNoteAttachment,
    StudyNoteImage,
)
from apps.study_notes.tests.mock_s3_uploader import MockS3Uploader
from apps.users.models.user import User


class StudyNoteService:
    def __init__(self, s3_uploader: Optional[Union[S3Uploader, MockS3Uploader]] = None) -> None:
        # 실제 기능: None이면 S3Uploader() 사용, 테스트: MockS3Uploader 주입
        self.s3: Union[S3Uploader, MockS3Uploader] = s3_uploader or S3Uploader()

    def create_study_note(
        self,
        author: User,
        study_group: StudyGroup,
        title: str,
        content: str,
        images: Optional[list[UploadedFile]] = None,
        attachments: Optional[list[UploadedFile]] = None,
    ) -> StudyNote:

        with transaction.atomic():
            note = StudyNote.objects.create_note(
                author=author,
                study_group=study_group,
                title=title,
                content=content,
            )
            # 트랜젝션(이미지에서 오류나면 전체 롤백)
            # 이미지 업로드
            if images:
                image_objs: List[StudyNoteImage] = []
                for img_file in images:
                    try:
                        s3_data = self.s3.upload_file(img_file)
                        image_objs.append(StudyNoteImage(study_note=note, img_url=s3_data["url"]))
                    except Exception as e:
                        # 예외 발생 시 업로드 실패 파일명 명시
                        raise RuntimeError(f"이미지 업로드 실패: {img_file.name}, error: {e}")
                StudyNoteImage.objects.bulk_create(image_objs)

            # 첨부파일 업로드
            if attachments:
                attachment_objs: List[StudyNoteAttachment] = []
                for attach_file in attachments:
                    try:
                        s3_data = self.s3.upload_file(attach_file)
                        attachment_objs.append(
                            StudyNoteAttachment(
                                study_note=note,
                                file_name=attach_file.name or "untitled",
                                file_url=s3_data["url"],
                            )
                        )
                    except Exception as e:
                        # 예외 발생 시 업로드 실패 파일명 명시
                        raise RuntimeError(f"첨부파일 업로드 실패: {attach_file.name}, error: {e}")
                StudyNoteAttachment.objects.bulk_create(attachment_objs)

            return note
