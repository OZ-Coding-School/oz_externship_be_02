from rest_framework import serializers

from ..models.recruitment_attachments import RecruitmentAttachment
from ..models.recruitments import Recruitment


class AttachmentUpdateSerializer(serializers.ModelSerializer[RecruitmentAttachment]):
    class Meta:
        model = RecruitmentAttachment
        fields = ["file_name", "file_url"]
        extra_kwargs = {
            "file_name": {"write_only": True},
            "file_url": {"write_only": True},
        }


class RecruitmentUpdateSerializer(serializers.ModelSerializer[Recruitment]):
    # 공고 수정을 위한 데이터 유효성 검증. 비즈니스 로직 포함 x
    tags = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    attachments = AttachmentUpdateSerializer(many=True, required=False, write_only=True)
    images = serializers.ListField(child=serializers.URLField(), required=False, write_only=True)

    class Meta:
        model = Recruitment
        fields = [
            "title",
            "content",
            "expected_headcount",
            "estimated_fee",
            "tags",
            "close_at",
            "attachments",
            "images",
        ]
