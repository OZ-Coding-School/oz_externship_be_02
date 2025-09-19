from datetime import date
from typing import Any
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITransactionTestCase

from apps.users.models.user import User


class RecruitmentFileUploadViewTest(APITransactionTestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com", password="password123", birthday=date(2000, 1, 1), phone_number="010-1234-5678"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("recruitment-file-upload")

    @patch("apps.recruitments.views.attachments_views.S3Uploader")
    def test_file_upload_success(self, mock_s3_uploader_class:Any) -> None:
        # GIVEN
        mock_s3_instance = mock_s3_uploader_class.return_value
        mock_s3_instance.upload_file.return_value = {
            "url": "https://s3.mock-domain.com/attachments/test.pdf"
        }
        test_file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        data = {"file": test_file}

        # WHEN
        response = self.client.post(self.url, data=data, format="multipart")

        # THEN
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["file_url"], "https://s3.mock-domain.com/attachments/test.pdf")

    def test_file_upload_fail_no_file(self) -> None:
        # GIVEN
        data: dict[str, Any] = {}
        # WHEN
        response = self.client.post(self.url, data=data, format="multipart")
        # THEN
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
