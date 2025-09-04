from rest_framework import serializers
from rest_framework.relations import StringRelatedField
from apps.lectures.models.crawled_lectures import Lecture
from apps.recruitments.models.recruitments import Recruitment
from apps.recruitments.models.tags import Tag

# 비직관적인 이름 변경과 다대다 관계 처리
class LectureSerializer(serializers.ModelSerializer[Lecture]):
    class Meta:
        model = Lecture
        fields = ("title", "instructor")


class RecruitmentSerializer(serializers.ModelSerializer[Recruitment]):
    # 썸네일 이미지: 조회할 때 추가 ( 첫번째 이미지, 없는 경우 기본 )
    img = serializers.URLField(read_only=True)

    # 하위에서 비직관적인 이름 변경과 다대다 관계 처리, 강의 목록 ( 강의명, 강사명 )
    # recruiments-study_groups-study_lectures-crawled_lectures > study_group__lectures로 최적화
    # queryset.select_related('study_group').prefetch_related('study_group__lectures')
    # 쿼리 최적화에 사용( https://docs.djangoproject.com/en/5.2/ref/models/querysets/#only )
    lectures = serializers.SerializerMethodField(read_only=True)

    # tags는 Tag의 str이용
    tags: StringRelatedField[Tag] = serializers.StringRelatedField(many=True, read_only=True)

    # bookmarks_count는 bookmark_users의 개수만 받기 ( 조회 때 추가 )
    bookmarks_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Recruitment
        fields = (
            "id",
            "title",
            "img",
            "expected_headcount",
            "lectures",
            "tags",
            "close_at",
            "views_count",
            "bookmarks_count",
        )

    def get_lectures(self, obj: Recruitment)-> list[object]:
        lectures=obj.study_group.lectures.all()
        serializer = LectureSerializer(lectures, many=True)
        return list(serializer.data)
