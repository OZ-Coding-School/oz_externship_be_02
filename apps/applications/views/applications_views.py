from typing import Any, cast
from uuid import UUID

from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import Application
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
    """
    지원서 생성(POST) 및 특정 공고의 지원자 목록 조회(GET)를 처리하는 View
    """

    def get_permissions(self) -> list[BasePermission]:
        if self.request.method == "GET":
            return [IsAuthenticated(), IsRecruitmentAuthor()]
        return [IsAuthenticated()]

    def get(self, request: Request, recruitment_uuid: UUID) -> Response:
        """특정 공고에 대한 지원자 목록을 조회한다."""
        # IsRecruitmentAuthor permission에서 이미 recruitment 객체를 조회하여 request에 담아주므로 DB를 다시 조회할 필요가 없습니다.
        recruitment = request.recruitment
        queryset = Application.objects.get_applications_for_recruitment(recruitment_uuid=recruitment.uuid)

        paginator = DefaultCursorPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)

        serializer = RecruitmentApplicationListSerializer(paginated_queryset, many=True)

        paginated_data = cast(list[dict[str, Any]], serializer.data)

        return paginator.get_paginated_response(paginated_data)

    def post(self, request: Request, recruitment_uuid: UUID) -> Response:
        """지원서 생성 요청(POST)을 처리한다."""
        try:
            recruitment = Recruitment.objects.get(uuid=recruitment_uuid)
        except Recruitment.DoesNotExist:
            return Response(
                {"error_code": "RECRUITMENT_NOT_FOUND", "message": "해당 스터디 공고를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ApplicationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error_code": "INVALID_INPUT", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = cast(User, request.user)
            service = ApplicationService()
            application = service.create_application(user=user, recruitment=recruitment, **serializer.validated_data)
        except IntegrityError as e:
            return Response({"error_code": "DUPLICATE_APPLICATION", "message": str(e)}, status=status.HTTP_409_CONFLICT)

        return Response(
            {"application_id": application.id, "message": "스터디 공고 참여 신청 성공"}, status=status.HTTP_201_CREATED
        )
