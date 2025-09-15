from typing import Sequence

from django.core.files.uploadedfile import UploadedFile
from rest_framework import serializers

from apps.study_notes.models.study_notes import (
    StudyNote,
    StudyNoteAttachment,
    StudyNoteImage,
)


class StudyNoteImageSerializer(serializers.ModelSerializer[StudyNoteImage]):
    class Meta:
        model = StudyNoteImage
        fields = ["id", "img_url"]


class StudyNoteAttachmentSerializer(serializers.ModelSerializer[StudyNoteAttachment]):
    class Meta:
        model = StudyNoteAttachment
        fields = ["id", "file_name", "file_url"]


class StudyNoteSerializer(serializers.ModelSerializer[StudyNote]):
    images = StudyNoteImageSerializer(many=True, read_only=True)
    attachments = StudyNoteAttachmentSerializer(many=True, read_only=True)
    images_file: serializers.ListField = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    attachments_file: serializers.ListField = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )

    class Meta:
        model = StudyNote
        fields = [
            "id",
            "study_group",
            "author",
            "title",
            "content",
            "images",
            "images_file",
            "attachments",
            "attachments_file",
            "ai_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "study_group", "author", "ai_summary", "created_at", "updated_at"]

    # 이미지 유효성 검사
    def validate_images_file(self, files: Sequence[UploadedFile]) -> Sequence[UploadedFile]:
        if len(files) > 5:
            raise serializers.ValidationError("이미지는 최대 5개까지 업로드 가능합니다.")
        for f in files:
            if f.size is not None and f.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(f"{f.name}: 이미지는 5MB 이하만 업로드 가능합니다.")
            if f.content_type not in ["image/jpeg", "image/png"]:
                raise serializers.ValidationError(f"{f.name}: JPEG, PNG만 업로드 가능합니다.")
        return files

    # 첨부파일 유효성 검사
    def validate_attachments_file(self, files: Sequence[UploadedFile]) -> Sequence[UploadedFile]:
        if len(files) > 3:
            raise serializers.ValidationError("첨부파일은 최대 3개까지 업로드 가능합니다.")
        for f in files:
            if f.size is not None and f.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(f"{f.name}: 첨부파일은 5MB 이하만 업로드 가능합니다.")
            if f.content_type not in ["application/pdf", "application/msword"]:
                raise serializers.ValidationError(f"{f.name}: PDF, DOC만 업로드 가능합니다.")
        return files
