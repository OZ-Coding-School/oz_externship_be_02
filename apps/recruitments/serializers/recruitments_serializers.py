from rest_framework import serializers

from ..models.recruitment_attachments import RecruitmentAttachment
from ..models.recruitments import Recruitment


class AttachmentSerializer(serializers.ModelSerializer[RecruitmentAttachment]):
    class Meta:
        model = RecruitmentAttachment
        fields = ["file_name", "file_url"]


class RecruitmentDetailSerializer(serializers.ModelSerializer[Recruitment]):
    author = serializers.SerializerMethodField()
    attachments = AttachmentSerializer(many=True, read_only=True)
    bookmark_count = serializers.SerializerMethodField()
    study_lectures = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Recruitment
        fields = [
            "id",
            "uuid",
            "author",
            "title",
            "content",
            "expected_headcount",
            "estimated_fee",
            "study_lectures",
            "tags",
            "attachments",
            "created_at",
            "updated_at",
            "close_at",
            "is_closed",
            "views_count",
            "bookmark_count",
        ]

    def get_author(self, obj: Recruitment) -> dict[str, str | int] | None:
        if obj.author:
            return {
                "id": obj.author.id,
                "nickname": obj.author.nickname,
            }
        return None

    def get_bookmark_count(self, obj: Recruitment) -> int:
        return obj.bookmark_users.count()

    def get_study_lectures(self, obj: Recruitment) -> list[dict[str, str | int]]:
        return [
            {
                "thumbnail_image_url": "https://example.com/thumbnail1.jpg",
                "name": "Django 기본 강좌",
                "instructor": "최재현",
                "shortcut_link": "https://example.com/lecture/1",
            }
        ]

    def get_tags(self, obj: Recruitment) -> list[str]:
        tags_list: list[str] = [tag.name for tag in obj.tags.all()]
        return tags_list
