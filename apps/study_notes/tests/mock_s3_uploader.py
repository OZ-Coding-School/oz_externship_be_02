from typing import BinaryIO

from django.core.files.uploadedfile import UploadedFile

from apps.core.utils.uploader_protocol import Uploader


class MockS3Uploader(Uploader):
    """테스트용 S3 업로더"""

    def upload_file(self, file: BinaryIO | UploadedFile) -> dict[str, str]:
        """파일을 업로드하고 S3 URL을 반환하는 척합니다."""
        filename = file.name if file.name else "unknown_file"
        return {"url": f"https://mock_s3_url.com/{filename}", "key": filename}
