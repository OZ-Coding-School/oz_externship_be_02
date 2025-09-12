from typing import List, Optional

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

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
        # 실제 기능: None이면 S3Uploader() 사용, 테스트: MockS3Uploader 주입
        self.s3: S3Uploader = s3_uploader or S3Uploader()

    def create_study_note(
        self,
        author: User,
        study_group: StudyGroup,
        title: str,
        content: str,
        images: Optional[list[UploadedFile]] = None,
        attachments: Optional[list[UploadedFile]] = None,
    ) -> StudyNote:

        uploaded_keys: List[str] = []  # 롤백 시 삭제할 key 모음

        # 트랜젝션(이미지에서 오류나면 전체 롤백)
        # 이미지 업로드

        try:
            with transaction.atomic():
                note = StudyNote.objects.create_note(
                    author=author,
                    study_group=study_group,
                    title=title,
                    content=content,
                )

                # 이미지 업로드
                if images:
                    image_objs: List[StudyNoteImage] = []
                    for img_file in images:
                        try:
                            s3_data = self.s3.upload_file(img_file)
                            uploaded_keys.append(s3_data["key"])
                            image_objs.append(StudyNoteImage(study_note=note, img_url=s3_data["url"]))
                        except Exception as img_err:
                            raise RuntimeError(f"이미지 업로드 실패: {img_file.name}, error: {img_err}")
                    StudyNoteImage.objects.bulk_create(image_objs)

                # 첨부파일 업로드
                if attachments:
                    attachment_objs: List[StudyNoteAttachment] = []
                    for attach_file in attachments:
                        try:
                            s3_data = self.s3.upload_file(attach_file)
                            uploaded_keys.append(s3_data["key"])
                            attachment_objs.append(
                                StudyNoteAttachment(
                                    study_note=note,
                                    file_name=attach_file.name or "untitled",
                                    file_url=s3_data["url"],
                                )
                            )
                        except Exception as attach_err:
                            raise RuntimeError(f"첨부파일 업로드 실패: {attach_file.name}, error: {attach_err}")
                    StudyNoteAttachment.objects.bulk_create(attachment_objs)

                return note

        except Exception as e:
            # 롤백 시 업로드된 S3 객체 삭제 (고아 객체 방지)
            for key in uploaded_keys:
                try:
                    self.s3.delete_file(key)
                except Exception as del_err:
                    import logging

                    logger = logging.getLogger("django")
                    logger.warning(f"S3 객체 삭제 실패: {key}, error: {del_err}")

            raise RuntimeError(f"StudyNote 생성 실패, 롤백 완료. Error: {e}")
