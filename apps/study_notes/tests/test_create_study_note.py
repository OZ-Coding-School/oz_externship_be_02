from datetime import timedelta
from typing import cast

from django.contrib.auth import get_user_model
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
from apps.study_notes.services.study_notes_services import StudyNoteService
from apps.study_notes.tests.mock_s3_uploader import MockS3Uploader

User = get_user_model()


class TestStudyNoteAPI(TestCase):
    """
    StudyNote 생성 API 테스트
    - setUp: 테스트 환경 초기화 (유저, 그룹, 파일 생성)
    - test_create_study_note_success: 성공 케이스
    - test_create_study_note_missing_title_fail: 실패 케이스 (필수값 누락)
    """

    def setUp(self) -> None:
        self.client = APIClient()

        # 테스트 사용자 생성
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="password123",
            name="테스트유저",
            nickname="testnick",
            phone_number="010-1234-5678",
            gender="male",
            birthday="2000-01-01",
        )

        # 테스트 스터디 그룹 생성
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

    def test_create_study_note_success(self) -> None:
        """
        스터디 노트 생성 성공 케이스
        """
        # 테스트에서 MockS3Uploader 사용(실기능 시 S3Uploader 사용)
        service = StudyNoteService(s3_uploader=MockS3Uploader())

        data = {"title": "Test Note", "content": "스터디 노트 내용"}

        note = service.create_study_note(
            author=self.user,
            study_group=self.group,
            title=data["title"],
            content=data["content"],
            images=[self.image_file],  # 테스트 이미지 업로드
            attachments=[self.attachment_file],  # 테스트 파일 업로드
        )

        # DB 확인
        self.assertIsInstance(note, StudyNote)
        self.assertEqual(note.title, data["title"])
        self.assertEqual(note.content, data["content"])
        self.assertEqual(note.author, self.user)
        self.assertEqual(note.study_group, self.group)

        # 이미지 URL 확인
        first_image = cast(StudyNoteImage, note.images.first())
        self.assertEqual(first_image.img_url, "https://mock_s3_url.com/image1.png")

        # 첨부파일 URL 확인
        first_attachment = cast(StudyNoteAttachment, note.attachments.first())
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

    def test_create_study_note_api_coverage(self) -> None:
        """
        coverage 확보
        """
        payload = {"title": "Coverage Test", "content": "뷰 호출로 커버리지 확보"}

        # self.client.post로 APIView 호출, 파일 없이 간단히 테스트
        response = self.client.post(self.url, data=payload, format="multipart")

        # 성공 시 201 Created 확인
        # 실패 가능성이 있으면 validation 통과용 payload로 조정 가능
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
