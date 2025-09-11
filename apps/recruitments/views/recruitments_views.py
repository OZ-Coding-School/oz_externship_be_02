from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers.recruitments_serializers import (
    RecruitmentDetailSerializer,
)
from ..services.recruitments_services import get_recruitment_detail, update_recruitment


class RecruitmentDetailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    @extend_schema(
        summary="스터디 구인공고 상세조회",
        description="recruitment_uuid에 해당하는 스터디 구인공고의 모든 상세정보 조회",
        responses={
            status.HTTP_200_OK: RecruitmentDetailSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="해당 공고를 찾을 수 없음", response={"erros": "string"}
            ),
        },
        parameters=[
            OpenApiParameter(
                name="recruitment_uuid",
                type=UUID,
                location=OpenApiParameter.PATH,
                description="조회할 공고의 고유 UUID",
            ),
        ],
    )
    def get(self, request: Request, recruitment_uuid: UUID) -> Response:
        # GET 요청은 권한 검사가 전혀 필요 없으므로, 바로 로직을 실행합니다.
        try:
            recruitment = get_recruitment_detail(recruitment_uuid=recruitment_uuid)
        except ObjectDoesNotExist as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        serializer = RecruitmentDetailSerializer(recruitment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="스터디 구인 공고 수정 (PATCH method)",
        responses={
            status.HTTP_200_OK: RecruitmentDetailSerializer,
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description="인증이 필요합니다."),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(description="수정 권한이 없습니다."),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description="해당 공고를 찾을 수 없습니다."),
        },
        parameters=[
            OpenApiParameter(
                name="recruitment_uuid",
                type=UUID,
                location=OpenApiParameter.PATH,
                description="수정할 공고의 고유 UUID",
            ),
        ],
    )
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
