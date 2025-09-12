from datetime import timedelta
from typing import Any, Optional
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile  # 테스트용 파일 생성
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
from apps.study_notes.tests.mock_s3_uploader import MockS3Uploader
from apps.users.models.user import User


class TestStudyNoteAPI(TestCase):
    """
    StudyNote 생성 API 테스트
    - setUp: 테스트 환경 초기화 (유저, 그룹, 파일 생성)
    - test_create_study_note_success: 성공 케이스
    - test_create_study_note_missing_title_fail: 실패 케이스 (필수값 누락)
    """

    user: User
    group: StudyGroup

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="testuser@example.com",
            password="password123",
            name="테스트유저",
            nickname="testnick",
            phone_number="010-1234-5678",
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
        # 그룹에 맴버 추가
        self.group.members.add(self.user)
        # 인증
        self.client.force_authenticate(user=self.user)
        self.url = reverse("create-study-note", kwargs={"group_uuid": self.group.uuid})

        # 테스트용 파일 생성
        self.image_file = SimpleUploadedFile("image1.png", b"file_content", content_type="image/png")
        self.attachment_file = SimpleUploadedFile("file1.pdf", b"file_content", content_type="application/pdf")

    @patch("apps.study_notes.services.study_notes_services.S3Uploader", MockS3Uploader)
    def test_create_study_note_success(self) -> None:
        """
        StudyNote 생성 성공 케이스
        - 뷰의 post() 메서드 호출
        - 실제 API 요청으로 모델 생성 확인
        """
        data = {
            "title": "Test Note",
            "content": "스터디 노트 내용",
            "images": [self.image_file],
            "attachments": [self.attachment_file],
        }

        # API 요청
        response = self.client.post(self.url, data=data, format="multipart")

        # 상태 코드 확인
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # DB에서 실제 객체 확인
        note_id = response.json()["id"]
        note = StudyNote.objects.get(id=note_id)
        self.assertEqual(note.title, data["title"])
        self.assertEqual(note.content, data["content"])
        self.assertEqual(note.author, self.user)
        self.assertEqual(note.study_group, self.group)

        # 이미지/첨부파일 URL 확인
        first_image: Optional[StudyNoteImage] = note.images.first()
        if first_image:
            self.assertEqual(first_image.img_url, "https://mock_s3_url.com/image1.png")

        first_attachment: Optional[StudyNoteAttachment] = note.attachments.first()
        if first_attachment:
            self.assertEqual(first_attachment.file_url, "https://mock_s3_url.com/file1.pdf")

    def test_create_study_note_missing_title_fail(self) -> None:
        """
        필수값(title) 누락 시 실패
        """
        data = {"title": "", "content": "제목 없음"}

        response = self.client.post(self.url, data=data, format="multipart")

        # 400 Bad Request 확인
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.json())
