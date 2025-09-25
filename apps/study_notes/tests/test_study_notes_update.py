from datetime import datetime
from typing import cast
from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import (
    StudyNote,
    StudyNoteAttachment,
    StudyNoteImage,
)
from apps.study_notes.services.study_notes_services import StudyNoteService
from apps.users.models.user import User


class StudyNoteUpdateTestCase(TestCase):
    client: APIClient
    user: User
    other_user: User
    study_group: StudyGroup
    note: StudyNote
    image1: StudyNoteImage
    attachment1: StudyNoteAttachment
    service: StudyNoteService

    @classmethod
    def setUpTestData(cls) -> None:
        # 유저 & 그룹 생성
        cls.user = User.objects.create_user(
            email="user1@example.com",
            password="password123",
            name="테스트유저1",
            nickname="nick1",
            phone_number="01012345671",
            gender="남성",
            birthday="2000-01-01",
        )
        cls.other_user = User.objects.create_user(
            email="user2@example.com",
            password="password123",
            name="테스트유저2",
            nickname="nick2",
            phone_number="01012345672",
            gender="여성",
            birthday="2000-01-02",
        )
        cls.study_group = StudyGroup.objects.create(
            name="테스트그룹",
            max_headcount=5,
            start_at=timezone.make_aware(datetime(2025, 9, 16, 12, 0, 0)),
            end_at=timezone.make_aware(datetime(2025, 9, 30, 12, 0, 0)),
        )
        cls.study_group.members.add(cls.user)

        # 스터디 노트 + 이미지/첨부 생성
        cls.note = StudyNote.objects.create_note(
            author=cls.user, study_group=cls.study_group, title="노트 1", content="내용 1"
        )
        cls.image1 = cls.note.images.create(img_url="https://fake-s3.com/image1.png")
        cls.attachment1 = cls.note.attachments.create(file_name="file1.pdf", file_url="https://fake-s3.com/file1.pdf")

    def setUp(self) -> None:
        self.client = APIClient()
        self.service = StudyNoteService()
        self.note.refresh_from_db()

    # 1. 정상 수정 (기존 이미지 유지 + 새 이미지/첨부 추가)
    @patch("apps.study_notes.services.study_notes_services.generate_study_summary", return_value="MOCKED SUMMARY")
    @patch("apps.study_notes.services.study_notes_services.transaction.on_commit")
    def test_normal_update_with_files(self, mock_on_commit: Mock, mock_summary: Mock) -> None:
        self.client.force_authenticate(user=self.user)
        url = reverse("study-note-detail", kwargs={"group_uuid": str(self.study_group.uuid), "note_id": self.note.id})

        # 기존 이미지 URL 포함 + 새 이미지 URL 추가
        data = {
            "title": "수정된 제목",
            "content": "수정된 본문",
            "image_urls": [
                "https://fake-s3.com/image1.png",  # 기존 이미지 유지
                "https://fake-s3.com/new_img.png",  # 새 이미지 추가
            ],
            "attachment_urls": [
                {"file_name": "file1.pdf", "file_url": "https://fake-s3.com/file1.pdf"},  # 기존 첨부 유지
                {"file_name": "new_file.pdf", "file_url": "https://fake-s3.com/new_file.pdf"},  # 새 첨부 추가
            ],
        }

        response = self.client.patch(url, data, format="json")
        mock_on_commit.call_args.args[0]()  # 트랜잭션 커밋 후 AI 요약 강제 실행
        self.note.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.note.title, "수정된 제목")
        self.assertEqual(self.note.content, "수정된 본문")
        self.assertEqual(self.note.ai_summary, "MOCKED SUMMARY")
        self.assertEqual(self.note.images.count(), 2)  # 기존 1 + 새 1
        self.assertEqual(self.note.attachments.count(), 2)
        image = cast(StudyNoteImage, self.note.images.first())
        self.assertEqual(image.img_url, "https://fake-s3.com/image1.png")  # 기존 이미지 확인
        attachment = cast(StudyNoteAttachment, self.note.attachments.first())
        self.assertEqual(attachment.file_url, "https://fake-s3.com/file1.pdf")  # 기존 첨부 확인

    # 2. 기존 파일 삭제 테스트 (요청에 없는 파일 삭제)
    @patch("apps.study_notes.services.study_notes_services.transaction.on_commit")
    def test_update_removes_old_files(self, mock_on_commit: Mock) -> None:
        self.client.force_authenticate(user=self.user)
        url = reverse("study-note-detail", kwargs={"group_uuid": str(self.study_group.uuid), "note_id": self.note.id})

        # 기존 파일 없이 새 파일만 요청 -> 기존 파일 삭제
        data = {
            "title": "수정 후 제목",
            "content": "수정 후 내용",
            "image_urls": ["https://fake-s3.com/new_img.png"],  # 기존 image1 삭제
            "attachment_urls": [
                {"file_name": "new_file.pdf", "file_url": "https://fake-s3.com/new_file.pdf"}
            ],  # 기존 첨부 삭제
        }

        response = self.client.patch(url, data, format="json")
        mock_on_commit.call_args.args[0]()
        self.note.refresh_from_db()

        self.assertEqual(self.note.images.count(), 1)
        self.assertEqual(self.note.attachments.count(), 1)

        # mypy 안전하게 cast 사용
        image = cast(StudyNoteImage, self.note.images.first())
        self.assertEqual(image.img_url, "https://fake-s3.com/new_img.png")

        attachment = cast(StudyNoteAttachment, self.note.attachments.first())
        self.assertEqual(attachment.file_url, "https://fake-s3.com/new_file.pdf")

    # 3. 권한 없는 유저
    def test_update_unauthorized_user(self) -> None:
        self.client.force_authenticate(user=self.other_user)
        url = reverse("study-note-detail", kwargs={"group_uuid": str(self.study_group.uuid), "note_id": self.note.id})

        data = {"title": "권한 없는 수정"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, "노트 1")
        self.assertEqual(self.note.content, "내용 1")
