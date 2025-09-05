from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recruitments.models.recruitments import Recruitment
from apps.recruitments.serializers.recruitments_serializers import (
    RecruitmentDetailSerializer,
)


class RecruitmentDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, recruitment_id: int) -> Response:
        # 테이블 명세서대로 하기 -> model과 serializer 이용하면 해결될거에요
        try:
            # 1. URL 경로로 recruitment_id를 사용해 데이터베이스에 해당하는 Recruitment 객체 조회
            recruitment = (
                Recruitment.objects.select_related("author")
                .prefetch_related("tags", "attachments", "bookmark_users")
                .get(id=recruitment_id)
            )
        except Recruitment.DoesNotExist:
            return Response({"error": "해당 공고를 찾을 수 없음."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RecruitmentDetailSerializer(recruitment)
        return Response(serializer.data, status=status.HTTP_200_OK)
