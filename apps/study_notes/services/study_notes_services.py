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
                    content=content,
                    author_name=author.name or "작성자 미상",
                    date_str=note.created_at.strftime("%Y년 %-m월 %-d일 %A"),
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
        delete_s3_keys: List[str] = []

        # 삭제할 이미지 URL 수집
        if delete_image_ids:
            delete_s3_keys.extend(
                list(
                    StudyNoteImage.objects.filter(study_note=note, id__in=delete_image_ids)
                    .values_list("img_url", flat=True)
                )
            )

        # 삭제할 첨부파일 URL 수집
        if delete_attachment_ids:
            delete_s3_keys.extend(
                list(
                    StudyNoteAttachment.objects.filter(study_note=note, id__in=delete_attachment_ids)
                    .values_list("file_url", flat=True)
                )
            )

        # 새로 업로드된 파일의 S3 key 모음 (트랜잭션 실패 시 삭제용)
        uploaded_keys: List[str] = []
        if images:
            uploaded_keys.extend(url.split("/")[-1] for url in images)
        if attachments:
            uploaded_keys.extend(att["file_url"].split("/")[-1] for att in attachments)

        try:
            with transaction.atomic():
                if title is not None:
                    note.title = title
                if content is not None:
                    note.content = content
                    note.ai_summary = generate_study_summary(
                        content=content,
                        author_name=note.author.name,
                        date_str=note.created_at.strftime("%Y년 %-m월 %-d일 %A"),
                    )
                note.save()

                # 이미지 추가 (bulk)
                if images:
                    StudyNoteImage.objects.bulk_create([StudyNoteImage(study_note=note, img_url=url) for url in images])

                # 첨부파일 추가 (bulk)
                if attachments:
                    StudyNoteAttachment.objects.bulk_create([
                        StudyNoteAttachment(study_note=note, file_url=att["file_url"], file_name=att["file_name"])
                        for att in attachments
                    ])

                # 이미지 삭제 (bulk)
                if delete_image_ids:
                    StudyNoteImage.objects.filter(study_note=note, id__in=delete_image_ids).delete()

                # 첨부파일 삭제 (bulk)
                if delete_attachment_ids:
                    StudyNoteAttachment.objects.filter(study_note=note, id__in=delete_attachment_ids).delete()

            # 트랜잭션 성공 후, 삭제 대상 S3 파일 제거 (실패해도 DB 롤백과 별개)
            if delete_s3_keys:
                try:
                    self.s3.delete_files(delete_s3_keys)
                except Exception as e:
                    logger.warning(f"S3 삭제 실패: {delete_s3_keys}, error: {e}")

            return note

        except Exception as e:
            # 트랜잭션 실패 시, 새로 업로드된 파일 S3 삭제
            if uploaded_keys:
                try:
                    self.s3.delete_files(uploaded_keys)
                except Exception as del_err:
                    logger.warning(f"트랜잭션 실패로 S3 rollback 실패: {uploaded_keys}, error: {del_err}")
            raise RuntimeError(f"스터디 노트 수정 실패, 롤백 완료. Error: {e}")
