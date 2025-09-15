from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apps.study_notes.serializers.study_notes_serializers import StudyNoteSerializer


class TestStudyNoteSerializer(TestCase):
    """
    StudyNoteSerializer 유효성 검사 테스트
    - 이미지 / 첨부파일 검증 실패 케이스
    """

    def test_validate_images_file(self) -> None:
        """이미지 5개 초과 시 ValidationError 발생"""
        files = [SimpleUploadedFile(f"img{i}.png", b"x", content_type="image/png") for i in range(6)]
        serializer = StudyNoteSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_images_file(files)

    def test_validate_images_file_type(self) -> None:
        """JPEG/PNG 외 이미지 업로드 시 ValidationError 발생"""
        file = SimpleUploadedFile("img.gif", b"x", content_type="image/gif")
        serializer = StudyNoteSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_images_file([file])

    def test_validate_attachments_file_large(self) -> None:
        """첨부파일 5MB 초과 시 ValidationError 발생"""
        big_file = SimpleUploadedFile("file.pdf", b"x" * (6 * 1024 * 1024), content_type="application/pdf")
        serializer = StudyNoteSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_attachments_file([big_file])

    def test_validate_attachments_file_type(self) -> None:
        """PDF, DOC 외 첨부파일 업로드 시 ValidationError 발생"""
        file = SimpleUploadedFile("file.txt", b"x", content_type="text/plain")
        serializer = StudyNoteSerializer()
        with self.assertRaises(ValidationError):
            serializer.validate_attachments_file([file])
