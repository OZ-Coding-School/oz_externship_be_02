from datetime import datetime
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
from apps.users.models.user import User


class StudyNoteUpdateFullTestCase(TestCase):
    client: APIClient
    user: User
    other_user: User
    study_group: StudyGroup
    note: StudyNote
    image1: StudyNoteImage
    attachment1: StudyNoteAttachment

    @classmethod
    def setUpTestData(cls) -> None:
        # 유저 생성
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
        # 그룹 생성
        cls.study_group = StudyGroup.objects.create(
            name="테스트그룹",
            max_headcount=5,
            start_at=timezone.make_aware(datetime(2025, 9, 16, 12, 0, 0)),
            end_at=timezone.make_aware(datetime(2025, 9, 30, 12, 0, 0)),
        )
        cls.study_group.members.add(cls.user)
        cls.note = StudyNote.objects.create(
            study_group=cls.study_group,
            author=cls.user,
            title="노트 1",
            content="내용 1",
            ai_summary="요약 1",
        )
        # 테스트용 이미지/첨부파일 생성
        cls.image1 = cls.note.images.create(img_url="https://fake-s3.com/image1.png")
        cls.attachment1 = cls.note.attachments.create(file_name="file1.pdf", file_url="https://fake-s3.com/file1.pdf")

    def setUp(self) -> None:
        self.client = APIClient()
        self.note = self.note

    # 정상 수정
    @patch("apps.study_notes.services.study_notes_services.generate_study_summary", return_value="MOCKED SUMMARY")
    def test_normal_update_with_files(self, mock_summary: Mock) -> None:
        self.client.force_authenticate(user=self.user)
        url = reverse(
            "study-note-update",
            kwargs={"group_uuid": str(self.study_group.uuid), "note_id": self.note.id},
        )

        data = {
            "title": "수정된 제목",
            "content": "수정된 본문",
            "image_urls": ["https://fake-s3.com/new_img.png"],
            "attachment_urls": [{"file_name": "new_file.pdf", "url": "https://fake-s3.com/new_file.pdf"}],
        }
        response = self.client.patch(url, data, format="json")
        self.note.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.note.title, "수정된 제목")
        self.assertEqual(self.note.content, "수정된 본문")
        self.assertEqual(self.note.ai_summary, "MOCKED SUMMARY")
        # 기존 1개 + 새 1개 = 2개
        self.assertEqual(self.note.images.count(), 2)
        self.assertEqual(self.note.attachments.count(), 2)

    # 기존 파일 삭제 테스트
    @patch("apps.study_notes.services.study_notes_services.S3Uploader")
    def test_delete_files(self, mock_s3_class: Mock) -> None:
        mock_s3 = mock_s3_class.return_value
        mock_s3.delete_files.return_value = None

        self.client.force_authenticate(user=self.user)
        url = reverse(
            "study-note-update",
            kwargs={"group_uuid": str(self.study_group.uuid), "note_id": self.note.id},
        )
        data = {
            "delete_image_ids": [self.image1.id],
            "delete_attachment_ids": [self.attachment1.id],
        }
        response = self.client.patch(url, data, format="json")
        self.note.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.note.images.count(), 0)
        self.assertEqual(self.note.attachments.count(), 0)
        # S3 삭제 함수가 올바른 URL과 함께 호출되었는지 확인
        mock_s3.delete_files.assert_called_once_with(
            ["https://fake-s3.com/image1.png", "https://fake-s3.com/file1.pdf"]
        )

    # 권한 없는 유저
    def test_update_unauthorized_user(self) -> None:
        self.client.force_authenticate(user=self.other_user)
        url = reverse(
            "study-note-update",
            kwargs={"group_uuid": str(self.study_group.uuid), "note_id": self.note.id},
        )
        data = {"title": "권한 없는 수정"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.note.refresh_from_db()
        # 기존 데이터 변화 없음
        self.assertEqual(self.note.title, "노트 1")
        self.assertEqual(self.note.content, "내용 1")
