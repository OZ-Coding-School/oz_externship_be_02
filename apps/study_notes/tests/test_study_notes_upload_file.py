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
        self.study_group.members.add(self.user)
        self.client.force_authenticate(user=self.user)

    def test_upload_multiple_files_no_loop(self) -> None:
        """업로드 API - 반복문 없이 여러 파일 업로드 테스트"""

        from django.urls import reverse

        url = reverse("upload-study-note-files")

        # 이미지 3개 생성
        image_file1 = create_temp_image()
        image_file2 = create_temp_image()
        image_file3 = create_temp_image()

        # 첨부파일 3개 생성
        attachment_file1 = SimpleUploadedFile("test1.txt", b"hello world", content_type="text/plain")
        attachment_file2 = SimpleUploadedFile("test2.txt", b"hello world", content_type="text/plain")
        attachment_file3 = SimpleUploadedFile("test3.txt", b"hello world", content_type="text/plain")

        data = {
            "image_files": [image_file1, image_file2, image_file3],
            "attachment_files": [attachment_file1, attachment_file2, attachment_file3],
        }

        response = cast(Response, self.client.post(url, data, format="multipart"))

        # 검증
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["images"]), 3)
        self.assertEqual(len(response.data["attachments"]), 3)
