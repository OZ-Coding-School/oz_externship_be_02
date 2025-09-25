from typing import Any, Sequence

from django.core.files.uploadedfile import UploadedFile
from rest_framework import serializers

from apps.study_notes.constants import ALLOWED_ATTACHMENT_FILE_TYPES
from apps.study_notes.models.study_notes import (
    StudyNote,
    StudyNoteAttachment,
    StudyNoteImage,
)
from apps.users.models import User


class StudyNoteImageSerializer(serializers.ModelSerializer[StudyNoteImage]):
    class Meta:
        model = StudyNoteImage
        fields = ["id", "img_url"]


class StudyNoteAttachmentSerializer(serializers.ModelSerializer[StudyNoteAttachment]):
    class Meta:
        model = StudyNoteAttachment
        fields = ["id", "file_name", "file_url"]


class AttachmentInputSerializer(serializers.Serializer[dict[str, Any]]):
    file_name = serializers.CharField(max_length=255)
    file_url = serializers.URLField()


class UserInfoSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["id", "nickname", "profile_img_url"]


class StudyNoteSerializer(serializers.ModelSerializer[StudyNote]):
    author = UserInfoSerializer(read_only=True)
    images = StudyNoteImageSerializer(many=True, read_only=True)
    attachments = StudyNoteAttachmentSerializer(many=True, read_only=True)
    image_files: serializers.ListField = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )
    attachment_files: serializers.ListField = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = StudyNote
        fields = [
            "id",
            "study_group",
            "author",
            "title",
            "content",
            "images",
            "image_files",
            "attachments",
            "attachment_files",
            "ai_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "study_group", "ai_summary"]

    # 이미지 유효성 검사
    def validate_image_files(self, files: Sequence[UploadedFile]) -> Sequence[UploadedFile]:
        if len(files) > 5:
            raise serializers.ValidationError("이미지는 최대 5개까지 업로드 가능합니다.")
        for f in files:
            if f.size is not None and f.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(f"{f.name}: 이미지는 5MB 이하만 업로드 가능합니다.")
            if f.content_type not in ["image/jpeg", "image/png"]:
                raise serializers.ValidationError(f"{f.name}: JPEG, PNG만 업로드 가능합니다.")
        return files

    # 첨부파일 유효성 검사
    def validate_attachment_files(self, files: Sequence[UploadedFile]) -> Sequence[UploadedFile]:
        if len(files) > 3:
            raise serializers.ValidationError("첨부파일은 최대 3개까지 업로드 가능합니다.")
        for f in files:
            if f.size is not None and f.size > 5 * 1024 * 1024:
                raise serializers.ValidationError(f"{f.name}: 첨부파일은 5MB 이하만 업로드 가능합니다.")
            if f.content_type not in ALLOWED_ATTACHMENT_FILE_TYPES:
                raise serializers.ValidationError(f"{f.name}: 지원하지 않는 파일 형식입니다.")
        return files


# 스터디 노트 기록 전체 목록 조회
class StudyNoteListSerializer(serializers.ModelSerializer[StudyNote]):
    author = UserInfoSerializer(read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = StudyNote
        fields = ["id", "title", "author", "created_at"]


class StudyNoteUpdateSerializer(serializers.ModelSerializer[StudyNote]):
    title = serializers.CharField(required=False, max_length=50)
    content = serializers.CharField(required=False)
    image_urls = serializers.ListField(child=serializers.URLField(), required=False, write_only=True)
    attachment_urls = AttachmentInputSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = StudyNote
        fields = [
            "title",
            "content",
            "image_urls",
            "attachment_urls",
        ]


class StudyNoteUploadSerializer(serializers.Serializer[dict[str, Any]]):
    image_files = serializers.ListField(child=serializers.ImageField(), write_only=True, required=False)
    attachment_files = serializers.ListField(child=serializers.FileField(), write_only=True, required=False)
