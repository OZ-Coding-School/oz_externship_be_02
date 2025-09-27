from typing import cast

from django.db.models import QuerySet
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.core.paginators import DefaultCursorPagination
from apps.users.models import User

from ..models import Application
from apps.applications.serializers.application_detail_serializers import MyApplicationDetailSerializer
from ..serializers.applications_list_serializers import MyApplicationListSerializer
from ..services.my_application_services import get_my_detail_aply, cancel_my_aply


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

# 나의 지원내역 상세페이지 기능 뷰
class MyDetailApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, application_id):
        my_aply=get_my_detail_aply(request.user, application_id)
        serializer = MyApplicationDetailSerializer(my_aply)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, application_id):
        result=cancel_my_aply(request.user, application_id)
        if result:
            return Response({"success": "지원을 취소했습니다."}, status=status.HTTP_200_OK)
        return Response({"fail":"대기 중 지원만 취소 가능합니다."}, status=status.HTTP_404_NOT_FOUND)