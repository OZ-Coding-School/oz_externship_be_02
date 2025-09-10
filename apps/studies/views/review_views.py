from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.serializers.review_serializers import ReviewCreateSerializer


class ReviewCreateAPIView(APIView):
    """
    [REQ-REVW-001] 스터디 그룹 리뷰 작성 API
    POST /api/v1/reviews/
    """

    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = ReviewCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            review = serializer.save()
            return Response(ReviewCreateSerializer(review).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
