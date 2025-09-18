from typing import Tuple
from uuid import UUID

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.models.study_groups import StudyGroup
from apps.studies.models.study_reviews import StudyReview
from apps.studies.serializers.review_serializers import (
    ReviewCreateRequestSerializer,
    ReviewCreateResponseSerializer,
    ReviewListResponseSerializer,
)


class ReviewCreateAPIView(APIView):
    """
    [REQ-REVW-001] 스터디 그룹 리뷰 작성 API
    POST /api/v1/reviews/
    """

    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        # 요청 검증
        request_serializer = ReviewCreateRequestSerializer(data=request.data, context={"request": request})
        if request_serializer.is_valid():
            # 저장
            review = request_serializer.save()

            # 응답 변환
            response_serializer = ReviewCreateResponseSerializer(review)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudyGroupReviewListView(APIView):
    """
    [REQ-REVW-00] 스터디 그룹 리뷰 목록 조회 API
    GET /api/v1/study-groups/reviews/{group_uuid}/
    - 로그인한 사용자가 특정 스터디 그룹의 리뷰 목록을 조회한다.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self, group_uuid: UUID) -> Tuple[StudyGroup, "QuerySet[StudyReview]"]:
        # 스터디 그룹 검증 (없으면 404)
        group = get_object_or_404(StudyGroup, uuid=group_uuid)

        # 리뷰 목록 조회 (없으면 빈 리스트 반환)
        qs = StudyReview.objects.filter(study_group=group).order_by("-created_at")
        return group, qs

    def get(self, request: Request, group_uuid: UUID, *args: object, **kwargs: object) -> Response:
        group, qs = self.get_queryset(group_uuid)
        payload = {"study_group_id": group.id, "reviews": qs}

        res = ReviewListResponseSerializer(payload, context={"request": request})
        return Response(res.data)
