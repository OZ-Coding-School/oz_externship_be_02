from rest_framework import serializers

from apps.study_notes.models.study_notes import StudyNote


class StudyNoteSerializer(serializers.ModelSerializer[StudyNote]):
    images = serializers.ListField(child=serializers.ImageField(), write_only=True, required=False)
    attachments = serializers.ListField(child=serializers.FileField(), write_only=True, required=False)

    class Meta:
        model = StudyNote
        fields = [
            "id",
            "study_group",
            "author",
            "title",
            "content",
            "images",
            "attachments",
            "ai_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "study_group", "author", "ai_summary", "created_at", "updated_at"]
