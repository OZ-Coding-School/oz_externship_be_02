from typing import cast

from django.db.models import QuerySet
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.serializers.application_detail_serializers import (
    MyApplicationDetailSerializer,
)
from apps.core.paginators import DefaultCursorPagination
from apps.users.models import User

from ..models import Application
from ..serializers.applications_list_serializers import MyApplicationListSerializer
from ..services.my_application_services import cancel_my_aply, get_my_detail_aply


class MyApplicationsListView(generics.ListAPIView[Application]):
    serializer_class = MyApplicationListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultCursorPagination

    def get_queryset(self) -> QuerySet[Application]:
        user = cast(User, self.request.user)
        queryset = (
            Application.objects.filter(user=user)
            .select_related("recruitment")
            .prefetch_related(
                "recruitment__tags",
                "recruitment__study_group__lectures",
                "recruitment__images",
            )
        )
        return queryset


class MyDetailApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["스터디 구인 공고"],
        summary="나의 지원 상세 조회",
        description="자신의 지원 내역에 대한 상세 조회를 진행할 수 있습니다.",
        responses={200: MyApplicationDetailSerializer},
    )
    def get(self, request: Request, application_id: int) -> Response:
        user = cast(User, request.user)
        my_aply = get_my_detail_aply(user, application_id)
        serializer = MyApplicationDetailSerializer(my_aply)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["스터디 구인 공고"],
        summary="나의 지원 취소",
        description="로그인한 사용자는 본인의 지원을 취소할 수 있습니다.\n\n"
        "이미 승인되거나 거절된 항목에 대해서는 취소할 수 없습니다.\n\n"
        "<참고 사항> 로그인한 사용자와 지원 내역 작성자가 달라도 상태주의 fail 텍스트 출력\n\n"
        "(보안강화, **대기중 상태인 지원 내역이 취소되지 않는다면 확인**)\n\n",
        responses={
            200: inline_serializer(
                name="cancel_success", fields={"success": serializers.CharField(default="지원을 취소했습니다.")}
            ),
            400: inline_serializer(
                name="cancel_fail", fields={"fail": serializers.CharField(default="대기 중 지원만 취소 가능합니다.")}
            ),
        },
    )
    def patch(self, request: Request, application_id: int) -> Response:
        user = cast(User, request.user)
        result = cancel_my_aply(user, application_id)
        if result:
            return Response({"success": "지원을 취소했습니다."}, status=status.HTTP_200_OK)
        return Response({"fail": "대기 중 지원만 취소 가능합니다."}, status=status.HTTP_400_BAD_REQUEST)
