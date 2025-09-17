from datetime import datetime
from typing import cast

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.core.utils.create_temp_image import create_temp_image
from apps.studies.models import StudyGroup
from apps.users.models.user import User


class StudyNoteUploadViewTest(TestCase):
    """StudyNoteUploadView 업로드 API 테스트"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            name="테스트유저",
            nickname="nicktest",
            phone_number="01012345678",
            gender="남성",
            birthday="2000-01-01",
        )
        self.study_group = StudyGroup.objects.create(
            name="테스트그룹",
            max_headcount=5,
            start_at=timezone.make_aware(datetime(2025, 9, 16, 12, 0, 0)),
            end_at=timezone.make_aware(datetime(2025, 9, 30, 12, 0, 0)),
        )
        self.client.force_authenticate(user=self.user)

    def test_upload_success(self) -> None:
        """업로드 API 정상 동작 테스트"""
        from django.urls import reverse

        url = reverse("upload-study-note-files", kwargs={"group_uuid": str(self.study_group.uuid)})

        image_file = create_temp_image()
        attachment_file = SimpleUploadedFile("test.txt", b"hello world", content_type="text/plain")
        data = {"images_file": [image_file], "attachments_file": [attachment_file]}  # 키 이름 수정

        response = cast(Response, self.client.post(url, data, format="multipart"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("images", response.data)
        self.assertIn("attachments", response.data)
        self.assertEqual(len(response.data["images"]), 1)
        self.assertEqual(len(response.data["attachments"]), 1)

    def test_create_note_view_success(self) -> None:
        """노트 생성 API 정상 동작 테스트"""
        from django.urls import reverse

        url = reverse("create-study-note", kwargs={"group_uuid": str(self.study_group.uuid)})

        image_file = create_temp_image()
        attachment_file = SimpleUploadedFile("test.txt", b"hello world", content_type="text/plain")
        data = {
            "title": "테스트 노트",
            "content": "본문 내용",
            "image_files": [image_file],
            "attachment_files": [attachment_file],
        }

        response = cast(Response, self.client.post(url, data, format="multipart"))
        self.assertIn(response.status_code, [200, 201])
        self.assertEqual(response.data.get("title"), "테스트 노트")
