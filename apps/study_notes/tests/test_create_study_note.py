from datetime import datetime, timedelta
from typing import cast

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import StudyNote
from apps.study_notes.services.study_notes_services import StudyNoteService

from ...core.utils.s3_uploader import S3Uploader
from .mock_s3_uploader import MockS3Uploader

User = get_user_model()


class TestCode(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="password",
            name="준혁",
            nickname="junhyuk",
            phone_number="01012345678",
            gender="남자",
            birthday="1990-01-01",
        )

        # 테스트용 스터디 그룹 생성
        now = timezone.now()
        self.group = StudyGroup.objects.create(
            name="Test Group",
            max_headcount=5,
            start_at=now,
            end_at=now + timedelta(days=30),
            status=StudyGroup.StatusChoices.PENDING,
        )
        # 그룹 멤버로 테스트 유저 추가
        self.group.members.add(self.user)

        self.client.force_authenticate(user=self.user)
        self.url = reverse("create-study-note", kwargs={"group_uuid": self.group.uuid})

        # 테스트용 서비스에 MockS3Uploader 주입
        self.service = StudyNoteService(s3_uploader=cast(S3Uploader, MockS3Uploader()))

    def test_create_study_note_false(self) -> None:
        """
        필수값에 대한 실패 테스트
        """
        payload = {
            "title": "",  # 필수값 누락
            "content": "오늘은 TDD 작성법에 대해 공부했습니다.",
        }

        # multipart 전송용 파일 dict
        files = {
            "images": SimpleUploadedFile("image1.png", b"file_content", content_type="image/png"),
            "attachments": SimpleUploadedFile("file1.pdf", b"file_content", content_type="application/pdf"),
        }
        response = self.client.post(self.url, data=payload, format="multipart", files=files)
        # 상태 코드 검증
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 응답 데이터 검증 - title 관련 에러 메시지 존재
        response_data = response.json()
        self.assertIn("title", response_data)

        # DB 데이터 검증
        self.assertFalse(StudyNote.objects.filter(content=payload["content"]).exists())

    def test_create_study_note_success(self) -> None:
        """
        스터디 노트 생성 성공 테스트
        """
        payload = {
            "title": "9월 04일 스터디 노트",
            "content": "오늘은 TDD 작성법에 대해 공부했습니다.",
        }

        # multipart 전송용 파일 dict
        files = {
            "images": SimpleUploadedFile("image1.png", b"file_content", content_type="image/png"),
            "attachments": SimpleUploadedFile("file1.pdf", b"file_content", content_type="application/pdf"),
        }

        note = self.service.create_study_note(
            author=self.user,
            study_group=self.group,
            title=payload["title"],
            content=payload["content"],
            images=[files["images"]],
            attachments=[files["attachments"]],
        )

        response = self.client.post(self.url, data=payload, format="multipart", files=files)

        # 상태 코드 검증
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 응답 데이터 검증
        response_data = response.json()
        self.assertEqual(response_data["title"], payload["title"])
        self.assertEqual(response_data["content"], payload["content"])

        # DB 데이터 검증 (RelatedManager 접근 시 .first() 사용)
        image = note.images.first()
        attachment = note.attachments.first()

        # None 체크
        assert image is not None
        assert attachment is not None

        # 체크한 변수를 사용
        self.assertEqual(image.img_url, "https://mock_s3_url.com/image1.png")
        self.assertEqual(attachment.file_url, "https://mock_s3_url.com/file1.pdf")
