from typing import Any, cast
from uuid import UUID

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.serializers.applications_list_serializers import (
    RecruitmentApplicationListSerializer,
)
from apps.applications.services.applications_list_services import (
    ApplicationListService,
)
from apps.core.paginators import DefaultCursorPagination
from apps.recruitments.recruitments_permissions import IsRecruitmentAuthor


class RecruitmentApplicationListView(APIView):
    """
    특정 공고에 대한 지원자 목록을 조회하는 View (GET 요청 처리)
    - APIView를 사용하여 페이지네이션을 직접 처리
    """

    permission_classes = [IsAuthenticated, IsRecruitmentAuthor]

    def get(self, request: Request, recruitment_uuid: UUID) -> Response:
        service = ApplicationListService()
        queryset = service.get_applications_for_recruitment(recruitment_uuid=recruitment_uuid)

        paginator = DefaultCursorPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)

        serializer = RecruitmentApplicationListSerializer(paginated_queryset, many=True)

        # mypy가 serializer.data의 타입을 list라고 확신하지 못하므로,
        # cast를 사용하여 개발자가 직접 타입을 명시해줍니다.
        paginated_data = cast(list[dict[str, Any]], serializer.data)

        return paginator.get_paginated_response(paginated_data)
