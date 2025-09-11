from typing import Any

from rest_framework import serializers

from apps.lectures.models.crawled_lectures import Lecture
from apps.users.models.user import User

from ..models.recruitment_attachments import RecruitmentAttachment
from ..models.recruitments import Recruitment
from ..models.tags import Tag


class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["id", "nickname"]


class AttachmentSerializer(serializers.ModelSerializer[RecruitmentAttachment]):
    class Meta:
        model = RecruitmentAttachment
        fields = ["file_name", "file_url"]


class TagSerializer(serializers.ModelSerializer[Tag]):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class LectureSerializer(serializers.ModelSerializer[Lecture]):
    name = serializers.CharField(source="title")
    shortcut_link = serializers.URLField(source="url_link")
    thumbnail_image_url = serializers.URLField(source="thumbnail_img_url")

    class Meta:
        model = Lecture
        fields = ["thumbnail_image_url", "name", "instructor", "shortcut_link"]


class RecruitmentDetailSerializer(serializers.ModelSerializer[Recruitment]):
    author = UserSerializer(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    study_lectures = LectureSerializer(many=True, read_only=True, source="study_group.lectures.all")
    bookmark_count = serializers.SerializerMethodField()

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

    @staticmethod
    def get_bookmark_count(obj: Recruitment) -> int:
        return obj.bookmark_users.count()

    # 공고 수정


class AttachmentUpdateSerializer(serializers.ModelSerializer[RecruitmentAttachment]):
    class Meta:
        model = RecruitmentAttachment
        fields = ["file_name", "file_url"]
        extra_kwargs = {
            "file_name": {"write_only": True},
            "file_url": {"write_only": True},
        }


class RecruitmentUpdateSerializer(serializers.ModelSerializer[Recruitment]):
    tags = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    attachments = AttachmentUpdateSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Recruitment
        fields = ["title", "content", "expected_headcount", "estimated_fee", "tags", "close_at", "attachments"]

    def update(self, instance: Recruitment, validated_data: dict[str, Any]) -> Recruitment:
        tag_names = validated_data.pop("tags", None)
        attachments_data = validated_data.pop("attachments", None)
        instance = super().update(instance, validated_data)

        if tag_names is not None:
            instance.tags.clear()
            tags_to_add = [Tag.objects.get_or_create(name=name)[0] for name in tag_names]
            instance.tags.add(*tags_to_add)

        if attachments_data is not None:
            instance.attachments.all().delete()
            RecruitmentAttachment.objects.bulk_create(
                [RecruitmentAttachment(recruitment=instance, **item) for item in attachments_data]
            )
        return instance
