from rest_framework import serializers

from apps.study_notes.models.study_notes import StudyNote


class StudyNoteSerializer(serializers.ModelSerializer[StudyNote]):
    """
    스터디 노트 생성 시 사용되는 Serializer
    """

    # 여러 이미지가 들어올 수 있기 떄문에 ListField로 받음
    images = serializers.ListField(child=serializers.URLField(), write_only=True, required=False)
    # 여러 첨부파일은 파일 이름도 같이 들어오기 때문에 DictField로 받음
    attachments = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()), write_only=True, required=False
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
            "attachments",
            "ai_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "study_group", "author", "ai_summary", "created_at", "updated_at"]
