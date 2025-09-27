from rest_framework import serializers

from ..models import Recruitment
from .recruitments_serializers import LectureSerializer, TagSerializer


class MyBookmarkedRecruitmentListSerializer(serializers.ModelSerializer[Recruitment]):
    lectures = LectureSerializer(many=True, read_only=True, source="study_group.lectures")
    tags = TagSerializer(many=True, read_only=True)
    thumbnail_image_url = serializers.SerializerMethodField()
    bookmark_count = serializers.IntegerField(source="bookmark_users.count")

    class Meta:
        model = Recruitment
        fields = [
            "uuid",
            "title",
            "thumbnail_image_url",
            "expected_headcount",
            "lectures",
            "tags",
            "close_at",
            "views_count",
            "bookmark_count",
        ]

    def get_thumbnail_image_url(self, obj: Recruitment) -> str | None:
        first_image = obj.images.first()
        if first_image:
            return first_image.img_url
        return None
