from typing import Dict,Optional,List

from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import (
    StudyNote,
    StudyNoteAttachment,
    StudyNoteImage,
)
from apps.users.models.user import User

# from core.utils.s3uploader import S3Uploader


class StudyNoteService:
    def create_study_note(
        self,
        author: User,
        study_group: StudyGroup,
        title: str,
        content: str,
        images: Optional[List] = None, # Optional 값이 있을 수도 있고 없을 수도 있다는 것을 알려주는 역할
        attachments: Optional[List[Dict[str, any]]] = None, # {"file_name": "a.pdf", "file_path": "/tmp/a.pdf"}
    ) -> StudyNote:
        """
        스터디 노트 생성 + S3 업로드
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
            image_objs = [] # bulk_create를 임시 리스트 생성
            for img_path in images:
                s3_url = self.s3.upload_file(img_path)  # S3에 업로드 후 URL 반환
                image_objs.append(StudyNoteImage(study_note=note, img_url=s3_url))

            StudyNoteImage.objects.bulk_create(image_objs) # bulk_create로 한 번에 저장

        # 파일 저장
        if attachments:
            attachment_objs = [] # bulk_create를 임시 리스트 생성
            for attach in attachments:
                s3_url = self.s3.upload_file(attach["file_path"])
                attachment_objs.append(
                    StudyNoteAttachment(
                        study_note=note,
                        file_name=attach["file_name"],
                        file_url=s3_url,
                    )
                )

            StudyNoteAttachment.objects.bulk_create(attachment_objs)

        return note

