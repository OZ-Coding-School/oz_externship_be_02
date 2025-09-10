from typing import Any

from django.core.files.uploadedfile import UploadedFile


class MockS3Uploader:
    """테스트용 S3 업로더"""

    def upload_file(self, file: UploadedFile | Any) -> dict[str, str]:
        filename = getattr(file, "name", "unknown_file")
        return {"url": f"https://mock_s3_url.com/{filename}", "key": filename}
