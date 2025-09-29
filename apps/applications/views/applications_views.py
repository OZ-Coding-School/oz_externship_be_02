from typing import Any, cast
from uuid import UUID

from django.db import IntegrityError
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import Application
from apps.applications.serializers.application_serializers import (
    ApplicationCreateResponseSerializer,
)
from apps.applications.serializers.application_serializers import (
    ErrorResponseSerializer,
)
from apps.applications.serializers.application_serializers import (
    ApplicationCreateSerializer,
)
from apps.applications.serializers.applications_list_serializers import (
    RecruitmentApplicationListSerializer,
)
from apps.applications.services import ApplicationService
from apps.core.paginators import DefaultCursorPagination
from apps.recruitments.models import Recruitment
from apps.recruitments.recruitments_permissions import IsRecruitmentAuthor
from apps.users.models import User


class ApplicationAPIView(APIView):
    def get_permissions(self) -> list[BasePermission]:
        if self.request.method == "GET":
            return [IsAuthenticated(), IsRecruitmentAuthor()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="REQ-APLY-002: 내 공고 지원자 목록 조회",
        tags=["스터디 공고 지원"],
        parameters=[
            OpenApiParameter(name="cursor", description="다음 페이지를 가리키는 커서 값", type=str),
            OpenApiParameter(name="limit", description="한 페이지에 표시할 항목의 수", type=int),
        ],
        responses={status.HTTP_200_OK: RecruitmentApplicationListSerializer(many=True)},
    )
    def get(self, request: Request, recruitment_uuid: UUID) -> Response:
        try:
            recruitment = Recruitment.objects.get(uuid=recruitment_uuid)
        except Recruitment.DoesNotExist:
            return Response({"error": "해당 스터디 공고를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, recruitment)
        queryset = Application.objects.get_applications_for_recruitment(recruitment_uuid=recruitment.uuid)
        paginator = DefaultCursorPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)
        serializer = RecruitmentApplicationListSerializer(paginated_queryset, many=True)
        paginated_data = cast(list[dict[str, Any]], serializer.data)
        return paginator.get_paginated_response(paginated_data)

    @extend_schema(
        summary="REQ-APLY-001: 스터디 공고 참여 신청",
        tags=["스터디 공고 지원"],
        request={"application/json": ApplicationCreateSerializer},
        responses={
            status.HTTP_201_CREATED: ApplicationCreateResponseSerializer,
            status.HTTP_404_NOT_FOUND: ErrorResponseSerializer,
            status.HTTP_409_CONFLICT: ErrorResponseSerializer,
        },
    )
    def post(self, request: Request, recruitment_uuid: UUID) -> Response:
        try:
            recruitment = Recruitment.objects.get(uuid=recruitment_uuid)
        except Recruitment.DoesNotExist:
            return Response(
                {"error": "해당 스터디 공고를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = cast(User, request.user)
        if Application.objects.has_applied(user=user, recruitment=recruitment):
            return Response({"error": "이미 해당 공고에 지원한 이력이 있습니다."}, status=status.HTTP_409_CONFLICT)

        serializer = ApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = ApplicationService()
        application = service.create_application(user=user, recruitment=recruitment, **serializer.validated_data)

        return Response(
            {"application_id": application.id, "message": "스터디 공고 참여 신청 성공"}, status=status.HTTP_201_CREATED
        )
