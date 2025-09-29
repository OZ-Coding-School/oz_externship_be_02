from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from apps.studies.models import StudyReview
from apps.studies.pagination import ReviewLimitOffsetPagination
from apps.studies.serializers.review_serializers import AdminReviewListSerializer


@extend_schema(
    tags=["Admin Reviews"],
    summary="관리자 리뷰 목록 조회 API",
    description="관리자 권한 유저가 스터디 리뷰 목록을 페이지네이션으로 조회. 사용자 닉네임/이메일 검색, 최신순/오래된순 정렬 지원.",
    responses={200: AdminReviewListSerializer(many=True)},
)
class AdminReviewListView(ListAPIView[StudyReview]):
    """
    관리자 리뷰 목록 조회 with offset
    """

    serializer_class: type[AdminReviewListSerializer] = AdminReviewListSerializer
    pagination_class = ReviewLimitOffsetPagination
    permission_classes = [IsAuthenticated, IsAdminUser]
    allowed_ordering_fields = ["created_at", "-created_at"]

    def get_queryset(self) -> QuerySet[StudyReview]:
        # 성능 최적화를 위해 select_related 사용 (N+1 쿼리 방지)
        queryset = StudyReview.objects.select_related("study_group", "user").all()

        # 검색 기능: 사용자 닉네임과 이메일 필터링
        user_nickname = self.request.query_params.get("user_nickname")
        user_email = self.request.query_params.get("user_email")
        if user_nickname:  # icontains로 대소문자 무시
            queryset = queryset.filter(user__nickname__icontains=user_nickname)
        if user_email:
            queryset = queryset.filter(user__email__icontains=user_email)

        # 정렬 기능: 기본 최신순 (-created_at), 쿼리 파라미터로 변경 가능 (URL?ordering=created_at -> 오래된 순)
        ordering = self.request.query_params.get("ordering", "-created_at")
        if ordering not in self.allowed_ordering_fields:
            ordering = "-created_at"
        queryset = queryset.order_by(ordering)

        return queryset
