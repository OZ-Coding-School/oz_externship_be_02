from datetime import timedelta
from typing import Any, Dict
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.studies.models import StudyGroup
from apps.study_notes.models import StudyNote
from apps.study_notes.services.study_notes_services import StudyNoteService
from apps.study_notes.tests.mock_s3_uploader import MockS3Uploader
from apps.users.models.user import User


class TestStudyNoteUploadAPI(TestCase):
    """
    스터디 노트 이미지/파일 업로드 API 테스트
    - 정상 업로드
    - 업로드 실패 (이미지/첨부)
    - 파일 없음
    """

    user: User
    group: StudyGroup

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="uploadtest@example.com",
            password="password123",
            name="테스트유저",
            nickname="uploadnick",
            phone_number="010-0000-0000",
            gender="male",
            birthday="2000-01-01",
        )

    def setUp(self) -> None:
        self.client = APIClient()
        self.group = StudyGroup.objects.create(
            name="Test Study Group",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=30),
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("upload-study-note-files", kwargs={"group_uuid": self.group.uuid})

        self.image_file = SimpleUploadedFile("image.png", b"content", content_type="image/png")
        self.attachment_file = SimpleUploadedFile("file.pdf", b"content", content_type="application/pdf")

    @patch("apps.study_notes.services.study_notes_services.S3Uploader", MockS3Uploader)
    def test_upload_success(self) -> None:
        """
        - 이미지/첨부 정상 업로드
        """
        data = {"images_file": [self.image_file], "attachments_file": [self.attachment_file]}
        response = self.client.post(self.url, data=data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("https://mock_s3_url.com/image.png", response.json()["images"])
        self.assertIn("https://mock_s3_url.com/file.pdf", [att["url"] for att in response.json()["attachments"]])

    @patch("apps.study_notes.services.study_notes_services.S3Uploader", MockS3Uploader)
    def test_upload_no_files(self) -> None:
        """
        - 파일 없이 요청 시 빈 리스트 반환
        """
        data: Dict[str, list[Any]] = {"images_file": [], "attachments_file": []}
        response = self.client.post(self.url, data=data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["images"], [])
        self.assertEqual(response.json()["attachments"], [])

    @patch("apps.study_notes.services.study_notes_services.S3Uploader.upload_file")
    def test_create_note_image_upload_fails(self, mock_upload: Any) -> None:
        """이미지 업로드 실패 시 StudyNote 생성되지 않고 RuntimeError 발생"""
        mock_upload.side_effect = RuntimeError("이미지 업로드 실패")
        service = StudyNoteService()

        with self.assertRaises(RuntimeError) as ctx:
            service.create_study_note(
                author=self.user,
                study_group=self.group,
                title="Test Note",
                content="내용",
                images=[self.image_file],
                attachments=[self.attachment_file],
            )

        self.assertIn("이미지 업로드 실패", str(ctx.exception))
        self.assertEqual(StudyNote.objects.count(), 0)  # Note가 생성되지 않아야 함

    @patch("apps.study_notes.services.study_notes_services.S3Uploader.upload_file")
    @patch("apps.study_notes.services.study_notes_services.S3Uploader.delete_file")
    def test_create_note_attachment_upload_fails(self, mock_delete: Any, mock_upload: Any) -> None:
        """
        - 이미지 업로드 성공 후 첨부파일 업로드 실패
        - 이전 업로드된 이미지가 delete_file 호출로 제거되는지 확인
        - RuntimeError 발생
        """
        mock_upload.side_effect = [
            {"key": "image_key", "url": "https://mock_s3_url.com/image.png"},
            RuntimeError("첨부파일 업로드 실패"),
        ]
        service = StudyNoteService()

        with self.assertRaises(RuntimeError):
            service.create_study_note(
                author=self.user,
                study_group=self.group,
                title="Test Note",
                content="내용",
                images=[self.image_file],
                attachments=[self.attachment_file],
            )

        # 이미지 삭제 호출 확인
        mock_delete.assert_called_with("image_key")
        self.assertEqual(StudyNote.objects.count(), 0)

    @patch("apps.study_notes.services.study_notes_services.S3Uploader.upload_file")
    def test_upload_file_failure_logging_only(self, mock_upload_file: Any) -> None:
        """
        - 파일 업로드 중 예외 발생
        - Response는 200
        - 실패 파일은 결과에서 제외됨
        """
        mock_upload_file.side_effect = Exception("S3 업로드 실패")

        dummy_file = SimpleUploadedFile("dummy.pdf", b"dummy content", content_type="application/pdf")

        response = self.client.post(self.url, {"attachments_file": [dummy_file]}, format="multipart")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["attachments"], [])
