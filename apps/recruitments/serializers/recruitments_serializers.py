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
    lecture_name = serializers.CharField(source="title")
    lecture_link = serializers.URLField(source="url_link")
    instructor_name = serializers.CharField(source="instructor")
    img_url = serializers.URLField(source="thumbnail_img_url")

    class Meta:
        model = Lecture
        fields = [
            "img_url",
            "lecture_name",
            "instructor_name",
            "lecture_link",
        ]


class RecruitmentDetailSerializer(serializers.ModelSerializer[Recruitment]):
    author = UserSerializer(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    study_lectures = LectureSerializer(many=True, read_only=True, source="study_group.lectures.all")
    bookmark_count = serializers.SerializerMethodField(read_only=True)

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


class RecruitmentUpdateSerializer(serializers.ModelSerializer[Recruitment]):
    tags = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    attachments = AttachmentSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Recruitment
        fields = ["title", "content", "expected_headcount", "estimated_fee", "tags", "close_at", "attachments"]
