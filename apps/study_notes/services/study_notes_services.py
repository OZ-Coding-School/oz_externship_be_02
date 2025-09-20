import logging
from typing import Dict, List, Optional

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from apps.core.utils.s3_uploader import S3Uploader
from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import (
    StudyNote,
    StudyNoteAttachment,
    StudyNoteImage,
)
from apps.study_notes.services.study_note_ai_summary import generate_study_summary
from apps.users.models.user import User

logger = logging.getLogger("django")


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
        image_urls: List[str] = []
        attachment_data: List[Dict[str, str]] = []

        # S3 업로드 먼저 진행 (트랜잭션 밖)
        try:
            if images:
                for img_file in images:
                    s3_data = self.s3.upload_file(img_file)
                    uploaded_keys.append(s3_data["key"])
                    image_urls.append(s3_data["url"])

            if attachments:
                for attach_file in attachments:
                    s3_data = self.s3.upload_file(attach_file)
                    uploaded_keys.append(s3_data["key"])
                    attachment_data.append({"file_name": attach_file.name or "untitled", "url": s3_data["url"]})

        except Exception as e:
            # 업로드 실패 시 이미 올라간 S3 객체 삭제
            try:
                self.s3.delete_files(uploaded_keys)
            except Exception as del_err:
                logger.warning(f"S3 객체 삭제 실패: {uploaded_keys}, error: {del_err}")
            raise RuntimeError(f"S3 업로드 실패, 롤백 완료. Error: {e}")

        # DB 트랜잭션 진행
        try:
            with transaction.atomic():
                note = StudyNote.objects.create_note(
                    author=author,
                    study_group=study_group,
                    title=title,
                    content=content,
                )

                # 이미지 DB 생성
                if image_urls:
                    image_objs = [StudyNoteImage(study_note=note, img_url=url) for url in image_urls]
                    StudyNoteImage.objects.bulk_create(image_objs)

                # 첨부파일 DB 생성
                if attachment_data:
                    attachment_objs = [
                        StudyNoteAttachment(study_note=note, file_name=d["file_name"], file_url=d["url"])
                        for d in attachment_data
                    ]
                    StudyNoteAttachment.objects.bulk_create(attachment_objs)

                # AI 요약본
                note.ai_summary = generate_study_summary(
                    content=content, author_name=author.name, date_str=note.created_at.strftime("%Y년 %-m월 %-d일 %A")
                )
                note.save(update_fields=["ai_summary"])

                return note

        except Exception as e:
            # DB 트랜잭션 실패 시 업로드된 S3 객체 삭제
            try:
                self.s3.delete_files(uploaded_keys)
            except Exception as del_err:
                logger.warning(f"S3 객체 삭제 실패: {uploaded_keys}, error: {del_err}")
            raise RuntimeError(f"StudyNote DB 생성 실패, 롤백 완료. Error: {e}")
