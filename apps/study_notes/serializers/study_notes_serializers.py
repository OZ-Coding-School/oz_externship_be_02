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
