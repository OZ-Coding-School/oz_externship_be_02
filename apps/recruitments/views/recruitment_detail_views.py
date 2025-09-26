from uuid import UUID

from django.db import transaction
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models.recruitments import Recruitment
from ..serializers.recruitments_serializers import (
    RecruitmentDetailSerializer,
    RecruitmentUpdateSerializer,
)
from ..services.recruitments_services import get_recruitment_detail


class RecruitmentDetailView(APIView):
    permission_classes = [AllowAny]  # 그냥 조회는 누구나 가능합니다
    authentication_classes = ()
    parser_classes = [JSONParser, MultiPartParser]

    @staticmethod
    def _get_object(recruitment_uuid: UUID) -> Recruitment:
        try:
            return Recruitment.objects.get(uuid=recruitment_uuid)
        except Recruitment.DoesNotExist:
            raise NotFound(f"Recruitment {recruitment_uuid} not found")

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
        recruitment = get_recruitment_detail(recruitment_uuid=recruitment_uuid)
        serializer = RecruitmentDetailSerializer(recruitment, context={"request": request})
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
        if not request.user.is_authenticated:
            return Response({"error": "인증이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        recruitment_to_update = self._get_object(recruitment_uuid=recruitment_uuid)

        if request.user != recruitment_to_update.author:
            return Response({"error": "이 공고를 수정할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        serializer = RecruitmentUpdateSerializer(instance=recruitment_to_update, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        return Response(
            RecruitmentDetailSerializer(updated_instance, context={"request": request}).data, status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="스터디 구인 공고 삭제",
        description="recruitment_uuid에 해당하는 구인공고 삭제, 작성자만 삭제 가능",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(description="삭제 성공. 응답 본문 없음."),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description="인증이 필요합니다."),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(description="삭제 권한이 없습니다."),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description="해당 공고를 찾을 수 없습니다."),
        },
        parameters=[
            OpenApiParameter(
                name="recruitment_uuid",
                type=UUID,
                location=OpenApiParameter.PATH,
                description="삭제할 공고의 고유 UUID",
            ),
        ],
    )
    def delete(self, request: Request, recruitment_uuid: UUID) -> Response:
        if not request.user.is_authenticated:
            return Response({"error": "인증이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        recruitment = self._get_object(recruitment_uuid)

        if request.user != recruitment.author:
            return Response({"error": "이 공고를 삭제할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            # 연결된 모든 지원 내역을 먼저 삭제
            recruitment.applications.all().delete()
            # 그 다음 공고를 삭제
            recruitment.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
