from django.db import models

from apps.core.models.base import BaseModel
from apps.recruitments.models.recruitments import Recruitment


class RecruitmentAttachment(BaseModel):
    # Recruitment.attachments
    recruitment = models.ForeignKey(
        Recruitment,
        on_delete=models.CASCADE,
        related_name="attachments",
        null=False,
        help_text="스터디 공고 ID",
    )
    # URLField -> FileField 로 변경, upload_to 경로 지정
    # FileField를 사용하여 사용자가 업로드한 '파일 자체'를 서버의 지정된 위치에 물리적으로 저장하는 역할. 파일이 저장될 '지정된 위치'는 setting에서 지정한다.
    file_url = models.FileField(upload_to="recruitment_attachments/%Y/%m/%d/", help_text="첨부파일")
    file_name = models.CharField(max_length=100, help_text="원본 파일명")  # 파일명은 별도 저장

    class Meta:
        db_table = "recruitment_attachments"

    def __str__(self) -> str:
        return self.file_name
