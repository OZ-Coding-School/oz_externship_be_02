from datetime import timedelta
from io import BytesIO
from typing import Any, Optional, Union, cast
from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile  # 테스트용 파일 생성
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.datastructures import MultiValueDict
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.utils.s3_uploader import S3Uploader
from apps.studies.models import StudyGroup
from apps.study_notes.models.study_notes import (
    StudyNote,
)
from apps.study_notes.services.study_notes_services import StudyNoteService
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

        # 테스트용 1x1 PNG 이미지 생성
        img_io = BytesIO()
        image = Image.new("RGB", (1, 1), color="white")
        image.save(img_io, "PNG")
        img_io.seek(0)
        self.image_file = SimpleUploadedFile("image1.png", img_io.read(), content_type="image/png")
        self.attachment_file = SimpleUploadedFile("file1.pdf", b"file_content", content_type="application/pdf")

    @patch("apps.study_notes.services.study_notes_services.S3Uploader", MockS3Uploader)
    def test_create_study_note_success(self) -> None:
        # MultiValueDict로 multipart/form-data 생성
        data: MultiValueDict[str, Any] = MultiValueDict()
        data.setlist("images_file", [self.image_file])
        data.setlist("attachments_file", [self.attachment_file])
        data["title"] = "Test Note"
        data["content"] = "스터디 노트 내용"

        response = self.client.post(self.url, data=data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        note = StudyNote.objects.get(id=response.json()["id"])
        self.assertEqual(note.title, "Test Note")
        self.assertEqual(note.content, "스터디 노트 내용")

        note_image = note.images.first()
        note_attachment = note.attachments.first()

        assert note_image is not None
        assert note_attachment is not None

        self.assertEqual(note_image.img_url, "https://mock_s3_url.com/image1.png")
        self.assertEqual(note_attachment.file_url, "https://mock_s3_url.com/file1.pdf")

    def test_create_study_note_missing_title_fail(self) -> None:
        """
        필수값(title) 누락 시 실패
        """
        data = {"title": "", "content": "제목 없음"}

        response = self.client.post(self.url, data=data, format="multipart")

        # 400 Bad Request 확인
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.json())

    @patch("apps.study_notes.services.study_notes_services.StudyNote.objects.create_note")
    @patch("apps.study_notes.services.study_notes_services.S3Uploader", MockS3Uploader)
    def test_create_study_note_db_failure_rollback(self, mock_create_note: Mock) -> None:
        """
        DB 저장 실패 시
        - 이미 업로드된 S3 객체 삭제
        - RuntimeError 발생
        """
        # create_note가 호출되면 무조건 예외 발생시키도록 설정
        mock_create_note.side_effect = Exception("DB 저장 실패")

        service = StudyNoteService(s3_uploader=cast(S3Uploader, MockS3Uploader()))

        with self.assertRaises(RuntimeError) as ctx:
            service.create_study_note(
                author=self.user,
                study_group=self.group,
                title="DB 실패 테스트",
                content="내용",
                images=[self.image_file],
                attachments=[self.attachment_file],
            )

        # 예외 메시지 확인
        self.assertIn("DB 생성 실패", str(ctx.exception))
        # DB에 남은 노트 없어야 함
        self.assertEqual(StudyNote.objects.count(), 0)
