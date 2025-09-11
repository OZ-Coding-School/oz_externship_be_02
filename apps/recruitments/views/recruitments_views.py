from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.recruitments_serializers import (
    RecruitmentDetailSerializer,
    RecruitmentUpdateSerializer,
)
from ..services.recruitments_services import get_recruitment_detail, update_recruitment


class RecruitmentDetailView(APIView):
    # [수정됨] 기본 권한은 '누구나'로 설정하여, 모든 요청이 일단 View 안으로 들어오게 합니다.
    # 이것이 405 에러를 피하는 가장 확실한 방법입니다.
    permission_classes = [AllowAny]
    authentication_classes = ()

    def get(self, request: Request, recruitment_uuid: UUID) -> Response:
        # GET 요청은 권한 검사가 전혀 필요 없으므로, 바로 로직을 실행합니다.
        try:
            recruitment = get_recruitment_detail(recruitment_uuid=recruitment_uuid)
        except ObjectDoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        serializer = RecruitmentDetailSerializer(recruitment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request: Request, recruitment_uuid: UUID) -> Response:

        # 1단계: 로그인 여부 확인
        if not request.user.is_authenticated:
            return Response(
                {"error": "인증이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED  # <-- 비로그인 시 401 에러
            )

        try:
            recruitment_to_update = get_recruitment_detail(recruitment_uuid=recruitment_uuid)
        except ObjectDoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        # 2단계: 작성자 본인 여부 확인
        if request.user != recruitment_to_update.author:
            return Response(
                {"error": "이 공고를 수정할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,  # <-- 작성자 아니면 403
            )

        # 모든 권한 검사를 통과한 경우 실행
        updated_recruitment = update_recruitment(recruitment=recruitment_to_update, data=request.data)

        response_serializer = RecruitmentDetailSerializer(updated_recruitment)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
