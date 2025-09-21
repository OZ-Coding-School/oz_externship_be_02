from typing import Any

from rest_framework import serializers

from apps.recruitments.models import RecruitmentAttachment


class RecruitmentAttachmentSerializer(serializers.ModelSerializer[RecruitmentAttachment]):
    class Meta:
        model = RecruitmentAttachment
        fields = ["id", "file_name", "file_url"]


class AttachmentPreUploadSerializer(serializers.Serializer[dict[str, Any]]):
    file = serializers.FileField(write_only=True)
