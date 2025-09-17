from datetime import datetime
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from PIL import Image
from rest_framework.exceptions import ValidationError

from apps.core.utils.create_temp_image import create_temp_image
from apps.studies.models import StudyGroup
from apps.study_notes.serializers.study_notes_serializers import StudyNoteSerializer
from apps.users.models.user import User


class StudyNoteSerializerTest(TestCase):
    """StudyNoteSerializer 유효성 검사"""

    def setUp(self) -> None:
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
        self.base_data = {"title": "테스트 제목", "content": "테스트 내용"}

    def test_image_validation_success(self) -> None:
        """이미지 파일 유효성 검사 성공"""
        image = create_temp_image()
        serializer = StudyNoteSerializer(data={**self.base_data, "image_files": [image]})
        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_image_too_many_fail(self) -> None:
        """이미지 파일 개수 초과 시 실패"""
        images = [create_temp_image() for _ in range(6)]
        serializer = StudyNoteSerializer(data={**self.base_data, "image_files": images})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_image_too_large_fail(self) -> None:
        """이미지 파일 크기 초과 시 실패"""
        img = Image.new("RGB", (100, 100))
        f = BytesIO()
        img.save(f, "jpeg")
        header = f.getvalue()
        large_image = SimpleUploadedFile("large.jpg", header + b"a" * (6 * 1024 * 1024), content_type="image/jpeg")
        serializer = StudyNoteSerializer(data={**self.base_data, "image_files": [large_image]})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_image_wrong_type_fail(self) -> None:
        """이미지 파일 형식 오류 시 실패"""
        wrong_file = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
        serializer = StudyNoteSerializer(data={**self.base_data, "image_files": [wrong_file]})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_attachment_validation_success(self) -> None:
        """첨부 파일 유효성 검사 성공"""
        attachment = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        serializer = StudyNoteSerializer(data={**self.base_data, "attachment_files": [attachment]})
        self.assertTrue(serializer.is_valid(raise_exception=True))

    def test_attachment_too_many_fail(self) -> None:
        """첨부 파일 개수 초과 시 실패"""
        attachments = [SimpleUploadedFile(f"t{i}.pdf", b"c", content_type="application/pdf") for i in range(4)]
        serializer = StudyNoteSerializer(data={**self.base_data, "attachment_files": attachments})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_attachment_too_large_fail(self) -> None:
        """첨부 파일 크기 초과 시 실패"""
        large_attachment = SimpleUploadedFile("large.pdf", b"a" * (6 * 1024 * 1024), content_type="application/pdf")
        serializer = StudyNoteSerializer(data={**self.base_data, "attachment_files": [large_attachment]})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_attachment_wrong_type_fail(self) -> None:
        """첨부 파일 형식 오류 시 실패"""
        wrong_file = SimpleUploadedFile("test.exe", b"content", content_type="application/octet-stream")
        serializer = StudyNoteSerializer(data={**self.base_data, "attachment_files": [wrong_file]})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
