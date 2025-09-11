from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.serializers.review_serializers import (
    ReviewCreateRequestSerializer,
    ReviewCreateResponseSerializer,
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
