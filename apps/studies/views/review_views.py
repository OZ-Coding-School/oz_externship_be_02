from typing import Any, cast
from uuid import UUID

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.models import StudyGroup, StudyReview
from apps.studies.permissions import IsReviewAuthor
from apps.studies.serializers.review_serializers import (
    ReviewCreateRequestSerializer,
    ReviewCreateResponseSerializer,
    ReviewListResponseSerializer,
    ReviewUpdateRequestSerializer,
    ReviewUpdateResponseSerializer,
)
from apps.users.models import User


class ReviewCreateListUpdateAPIView(APIView):
    """
    [REQ-REVW-001] 스터디 그룹 리뷰 작성 API
    POST /api/v1/study-groups/{group_uuid}/reviews
    [REQ-REVW-002] 스터디 그룹 리뷰 수정 API
    PATCH /api/v1/study-groups/{group_uuid}/reviews/{review_id}
    [REQ-REVW-000] 스터디 그룹 리뷰 목록 조회 API
    GET /api/v1/study-groups/{group_uuid}/reviews
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    # 리뷰 작성
    def post(self, request: Request, group_uuid: UUID) -> Response:
        user = cast(User, request.user)

        study_group = get_object_or_404(StudyGroup, uuid=group_uuid)

        if study_group.status != StudyGroup.StatusChoices.ENDED:
            return Response(
                {"error": "종료되지 않은 스터디 그룹에는 리뷰를 작성할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if StudyReview.objects.filter(user=user, study_group=study_group).exists():
            return Response(
                {"error": "이미 작성된 리뷰가 있습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_serializer = ReviewCreateRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        review = request_serializer.save(study_group=study_group, user=user)

        response_serializer = ReviewCreateResponseSerializer(review)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    # 리뷰 목록 조회
    def get_queryset(self, group_uuid: UUID) -> QuerySet[StudyReview]:
        return (
            StudyReview.objects.select_related("study_group")
            .filter(study_group__uuid=group_uuid)
            .order_by("-created_at")
        )

    def get(self, request: Request, group_uuid: UUID, *args: object, **kwargs: object) -> Response:
        if not StudyGroup.objects.filter(uuid=group_uuid).exists():
            return Response(
                {"error": "study_group_uuid invalid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.get_queryset(group_uuid)
        res = ReviewListResponseSerializer(qs, many=True)
        return Response(res.data, status=status.HTTP_200_OK)


class ReviewUpdateView(APIView):

    permission_classes = [IsAuthenticated, IsReviewAuthor]

    # 리뷰 수정
    def patch(self, request: Request, group_uuid: UUID, review_id: int, *args: Any, **kwargs: Any) -> Response:
        review = get_object_or_404(StudyReview, id=review_id, study_group__uuid=group_uuid)

        self.check_object_permissions(request, review)

        serializer = ReviewUpdateRequestSerializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_review = serializer.save()

        res = ReviewUpdateResponseSerializer(updated_review)
        return Response(res.data, status=status.HTTP_200_OK)
