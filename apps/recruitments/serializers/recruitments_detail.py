from rest_framework import serializers

from apps.lectures.models.crawled_lectures import Lecture
from apps.users.models.user import User

from ..models.recruitment_attachments import RecruitmentAttachment
from ..models.recruitment_images import RecruitmentImage
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


class ImageSerializer(serializers.ModelSerializer[RecruitmentImage]):
    class Meta:
        model = RecruitmentImage
        fields = ["id", "img_url"]


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
    images = ImageSerializer(many=True, read_only=True)
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
            "images",
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
