from typing import cast
from uuid import UUID

from django.db.models import QuerySet
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.models import StudyGroup, StudyReview
from apps.studies.serializers.review_serializers import (
    ReviewCreateRequestSerializer,
    ReviewCreateResponseSerializer,
    ReviewListResponseSerializer,
)
from apps.users.models import User


class ReviewCreateListAPIView(APIView):
    """
    [REQ-REVW-001] 스터디 그룹 리뷰 작성 API
    POST /api/v1/reviews
    [REQ-REVW-00] 스터디 그룹 리뷰 목록 조회 API
    GET /api/v1/study-groups/reviews/{group_uuid}
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request: Request, group_uuid: UUID) -> Response:
        user = cast(User, request.user)
        try:
            study_group = StudyGroup.objects.get(uuid=group_uuid)
        except StudyGroup.DoesNotExist:
            return Response(
                {"error": f"study group not found - uuid: {group_uuid}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if study_group.status != StudyGroup.StatusChoices.ENDED:
            return Response(
                {"error": "종료되지 않은 스터디 그룹에는 리뷰를 작성할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if StudyReview.objects.filter(user=user, study_group=study_group).exists():
            return Response({"error": "이미 작성된 리뷰가 있습니다."}, status=status.HTTP_400_BAD_REQUEST)

        request_serializer = ReviewCreateRequestSerializer(data=request.data)
        # 요청 데이터 검증
        request_serializer.is_valid(raise_exception=True)
        # 저장
        review = request_serializer.save(study_group=study_group, user=user)
        # 응답 변환
        response_serializer = ReviewCreateResponseSerializer(review)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self, group_uuid: UUID) -> QuerySet[StudyReview]:
        # 스터디 그룹 UUID를 통해 리뷰 목록 최신순 조회
        return (
            StudyReview.objects.select_related("study_group")
            .filter(study_group__uuid=group_uuid)
            .order_by("-created_at")
        )

    def get(self, request: Request, group_uuid: UUID, *args: object, **kwargs: object) -> Response:
        if not StudyGroup.objects.filter(uuid=group_uuid).exists():
            return Response({"error": "study_group_uuid invalid."}, status=status.HTTP_400_BAD_REQUEST)
        qs = self.get_queryset(group_uuid)
        res = ReviewListResponseSerializer(qs, many=True)
        return Response(res.data, status=status.HTTP_200_OK)
