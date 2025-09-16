from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def create_temp_image(
    color: tuple[int, int, int] = (255, 0, 0), size: tuple[int, int] = (200, 200), image_format: str = "png"
) -> SimpleUploadedFile:
    """
    메모리상에서 임시 이미지 생성
    :param color: 이미지 색상 (R, G, B)
    :param size: (width, height)
    :param image_format: PNG, JPEG 등
    :return: BytesIO 객체
    """
    file = BytesIO()
    image = Image.new("RGB", size, color)
    image.save(file, image_format)
    file.seek(0)  # 파일 포인터를 처음으로

    uploaded_file = SimpleUploadedFile(name="test.png", content=file.read(), content_type="image/png")
    return uploaded_file
