from typing import Any

from rest_framework import serializers

from apps.recruitments.models import RecruitmentImage


class RecruitmentImageSerializer(serializers.ModelSerializer[RecruitmentImage]):
    class Meta:
        model = RecruitmentImage
        fields = ["id", "img_url"]


class ImagePreUploadSerializer(serializers.Serializer[dict[str, Any]]):
    image = serializers.ImageField(write_only=True)
