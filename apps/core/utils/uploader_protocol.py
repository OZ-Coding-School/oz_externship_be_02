from typing import BinaryIO, Protocol

from django.core.files.uploadedfile import UploadedFile


class Uploader(Protocol):
    """Uploader 프로토콜"""

    def upload_file(self, file: BinaryIO | UploadedFile) -> dict[str, str]: ...
