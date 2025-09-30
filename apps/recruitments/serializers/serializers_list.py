from rest_framework import serializers
from rest_framework.relations import StringRelatedField

from apps.lectures.models.crawled_lectures import Lecture
from apps.recruitments.models.recruitments import Recruitment
from apps.recruitments.models.tags import Tag


# 비직관적인 이름(스터디그룹->강의) 변경
class LectureListSerializer(serializers.ModelSerializer[Lecture]):
    class Meta:
        model = Lecture
        fields = ("title", "instructor")


class RecruitmentListSerializer(serializers.ModelSerializer[Recruitment]):
    # 썸네일 이미지: 조회할 때 추가 ( 첫번째 이미지, 없는 경우 기본 )
    img = serializers.URLField()

    # 하위에서 비직관적인 이름 변경, 강의 목록 ( 강의명, 강사명 )
    # recruiments-study_groups-study_lectures-crawled_lectures > study_group__lectures로 최적화
    # queryset.select_related('study_group').prefetch_related('study_group__lectures')
    # 쿼리 최적화에 사용( https://docs.djangoproject.com/en/5.2/ref/models/querysets/#only )
    lectures = LectureListSerializer(source="study_group.lectures", many=True)

    # tags는 Tag의 str이용
    tags: StringRelatedField[Tag] = serializers.StringRelatedField(many=True)

    # bookmarks_count는 bookmark_users의 개수만 받기 ( 조회 때 추가 )
    bookmarks_count = serializers.IntegerField()

    class Meta:
        model = Recruitment
        fields = (
            "id",
            "uuid",
            "title",
            "img",
            "expected_headcount",
            "lectures",
            "tags",
            "close_at",
            "views_count",
            "bookmarks_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

# admin-application-detail시리얼라이저에서 활용
class RecruitmentApplicationSerializer(serializers.ModelSerializer[Recruitment]):
    lectures = LectureListSerializer(source="study_group.lectures", many=True)
    tags: StringRelatedField[Tag] = serializers.StringRelatedField(many=True)
    headcount=serializers.SerializerMethodField()
    class Meta:
        model = Recruitment
        fields = (
            "title",
            "headcount",
            "lectures",
            "close_at",
        )
        read_only_fields = fields

    def get_headcount(self, obj):
        return self.context.get("headcount",0)