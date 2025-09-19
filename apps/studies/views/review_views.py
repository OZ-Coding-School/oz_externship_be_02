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
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self, group_uuid: UUID) -> QuerySet[StudyReview]:
        return StudyReview.objects.filter(study_group__uuid=group_uuid).order_by("-created_at")

    def get(self, request: Request, group_uuid: UUID, *args: object, **kwargs: object) -> Response:
        qs = self.get_queryset(group_uuid)

        study_group_id = qs.values_list("study_group_id", flat=True).first()

        # 리뷰가 없으면 → StudyGroup 존재 여부 확인 후 id 가져오기
        if study_group_id is None:
            study_group_id = get_object_or_404(StudyGroup, uuid=group_uuid).id

        payload = {
            "study_group_id": study_group_id,
            "reviews": qs,
        }
        res = ReviewListResponseSerializer(payload, context={"request": request})
        return Response(res.data)
