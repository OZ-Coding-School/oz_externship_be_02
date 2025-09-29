from rest_framework import serializers

from apps.applications.models.applications import Application
from apps.recruitments.models import Recruitment

# 기존 serializers.py 파일에서 재사용할 시리얼라이저들을 import
# 이렇게 하면 코드를 중복해서 작성할 필요 X
from apps.recruitments.serializers.recruitments_serializers import (  # type: ignore[attr-defined]
    LectureSerializer,
    RecruitmentAttachmentSerializer,
    TagSerializer,
)


class ApplicationSerializer(serializers.ModelSerializer[Application]):
    # 관리자가 지원자의 기본 정보를 확인할 수 있도록 구성
    applicant_nickname = serializers.CharField(source="user.nickname", read_only=True)
    applicant_email = serializers.EmailField(source="user.email", read_only=True)
    applied_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Application
        fields = ["applicant_nickname", "applicant_email", "applied_at", "status"]


class AdminRecruitmentDetailSerializer(serializers.ModelSerializer[Recruitment]):
    # 재사용 시리얼라이저
    tags = TagSerializer(many=True, read_only=True)
    attachments = RecruitmentAttachmentSerializer(many=True, read_only=True)
    lectures = LectureSerializer(many=True, read_only=True, source="study_group.lectures.all")

    # 이 파일에서 새로 정의한 시리얼라이저
    applications = ApplicationSerializer(many=True, read_only=True)

    # 데이터 가공 및 계산이 필요한 필드
    status = serializers.SerializerMethodField()
    bookmark_count = serializers.SerializerMethodField()
    expected_payment_cost = serializers.SerializerMethodField()

    # 모델 필드와 JSON 필드 이름이 다른 경우
    views_count = serializers.IntegerField()

    class Meta:
        model = Recruitment
        fields = [
            "id",
            "uuid",
            "title",
            "content",
            "attachments",
            "estimated_fee",
            "expected_payment_cost",
            "lectures",
            "tags",
            "close_at",
            "status",
            "created_at",
            "updated_at",
            "views_count",
            "bookmark_count",
            "applications",
        ]
        extra_kwargs = {
            "views_count": {"read_only": True},
        }

    def get_status(self, obj: Recruitment) -> str:
        return "closed" if obj.is_closed else "recruiting"

    def get_bookmark_count(self, obj: Recruitment) -> int:
        return obj.bookmark_users.count()

    def get_expected_payment_cost(self, obj: Recruitment) -> int:
        if not hasattr(obj.study_group, "lectures"):
            return 0
        return sum(lecture.discount_price for lecture in obj.study_group.lectures.all())
