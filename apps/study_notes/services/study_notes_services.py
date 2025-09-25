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

    def _generate_ai_summary_on_commit(self, note: StudyNote, content: str) -> None:
        """트랜잭션 커밋 후 AI 요약 생성"""

        def update_summary() -> None:
            try:
                note.ai_summary = generate_study_summary(
                    content=content,
                    author_name=note.author.name,
                    date_str=note.created_at.strftime("%Y년 %-m월 %-d일 %A"),
                )
                note.save(update_fields=["ai_summary"])
            except Exception as e:
                logger.warning(f"AI 요약 생성 실패 (note_id={note.id}): {e}")

        transaction.on_commit(update_summary)

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
            try:
                self.s3.delete_files(uploaded_keys)
            except Exception as del_err:
                logger.warning(f"S3 객체 삭제 실패: {uploaded_keys}, error: {del_err}")
            raise RuntimeError(f"S3 업로드 실패, 롤백 완료. Error: {e}")

        try:
            with transaction.atomic():
                note = StudyNote.objects.create_note(
                    author=author,
                    study_group=study_group,
                    title=title,
                    content=content,
                )

                if image_urls:
                    StudyNoteImage.objects.bulk_create(
                        [StudyNoteImage(study_note=note, img_url=url) for url in image_urls]
                    )

                if attachment_data:
                    StudyNoteAttachment.objects.bulk_create(
                        [
                            StudyNoteAttachment(study_note=note, file_name=d["file_name"], file_url=d["url"])
                            for d in attachment_data
                        ]
                    )

            #  트랜잭션 후 AI 요약 생성
            self._generate_ai_summary_on_commit(note, content)

            return note

        except Exception as e:
            try:
                self.s3.delete_files(uploaded_keys)
            except Exception as del_err:
                logger.warning(f"S3 객체 삭제 실패: {uploaded_keys}, error: {del_err}")
            raise RuntimeError(f"StudyNote DB 생성 실패, 롤백 완료. Error: {e}")

    def update_study_note(
        self,
        note: StudyNote,
        title: Optional[str] = None,
        content: Optional[str] = None,
        images: Optional[list[str]] = None,  # 업로드 URL 리스트
        attachments: Optional[list[Dict[str, str]]] = None,  # {"file_name", "file_url"}
        delete_image_ids: Optional[list[int]] = None,
        delete_attachment_ids: Optional[list[int]] = None,
    ) -> StudyNote:
        """스터디 노트 수정"""

        # S3 삭제 대상 모음
        uploaded_keys: List[str] = []
        if images:
            uploaded_keys.extend(url.split("/")[-1] for url in images)
        if attachments:
            uploaded_keys.extend(att["file_url"].split("/")[-1] for att in attachments)

        try:
            with transaction.atomic():
                # 기존 이미지/첨부 중 요청에 없는 것 삭제
                if images is not None:
                    StudyNoteImage.objects.filter(study_note=note).exclude(img_url__in=images).delete()
                if attachments is not None:
                    requested_urls = [att["file_url"] for att in attachments]
                    StudyNoteAttachment.objects.filter(study_note=note).exclude(file_url__in=requested_urls).delete()

                # 제목/내용 업데이트
                if title is not None:
                    note.title = title
                if content is not None:
                    note.content = content
                if title is not None or content is not None:
                    note.save()

                # 새 이미지/첨부 추가
                if images:
                    existing_urls = set(note.images.values_list("img_url", flat=True))
                    new_images = [
                        StudyNoteImage(study_note=note, img_url=url) for url in images if url not in existing_urls
                    ]
                    if new_images:
                        StudyNoteImage.objects.bulk_create(new_images)

                if attachments:
                    existing_urls = set(note.attachments.values_list("file_url", flat=True))
                    new_attachments = [
                        StudyNoteAttachment(study_note=note, file_url=att["file_url"], file_name=att["file_name"])
                        for att in attachments
                        if att["file_url"] not in existing_urls
                    ]
                    if new_attachments:
                        StudyNoteAttachment.objects.bulk_create(new_attachments)

            # 트랜잭션 후 AI 요약 생성
            if content is not None:
                self._generate_ai_summary_on_commit(note, content)

            return note

        except Exception as e:
            if uploaded_keys:
                try:
                    self.s3.delete_files(uploaded_keys)
                except Exception as del_err:
                    logger.warning(f"트랜잭션 실패로 S3 rollback 실패: {uploaded_keys}, error: {del_err}")
            raise RuntimeError(f"스터디 노트 수정 실패, 롤백 완료. Error: {e}")
