from uuid import UUID

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.filters import UserFilter
from apps.users.models import User
from apps.users.permissons import IsSuperUser
from apps.users.serializers.admin_serializers import (
    UserAdminListSerializer,
    UserPermissionResponseSerializer,
    UserPermissionUpdateSerializer,
)


# 클래스 이름을 Update 기능에 집중하도록 변경 (선택사항이지만 권장)
class UserPermissionUpdateAPIView(APIView):
    # 이 API는 관리자(is_staff=True)만 접근 가능합니다.
    permission_classes = [IsSuperUser]

    def patch(self, request: Request, user_uuid: UUID) -> Response:
        # 1. 권한 변경 대상 유저 찾기
        target_user = get_object_or_404(User, uuid=user_uuid)

        # 2. 시리얼라이저로 데이터 유효성 검사 및 업데이트
        update_serializer = UserPermissionUpdateSerializer(
            instance=target_user, data=request.data, context={"request": request}
        )
        update_serializer.is_valid(raise_exception=True)
        updated_user = update_serializer.save()

        # 3. Response 시리얼라이저로 응답데이터 형성
        response_serializer = UserPermissionResponseSerializer(updated_user)
        return Response(
            {"detail": "권한이 성공적으로 변경되었습니다.", "data": response_serializer.data},
            status=status.HTTP_200_OK,
        )


# 페이지네이션 클래스 정의
class UserAdminPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class UserAdminViewSet(viewsets.ReadOnlyModelViewSet[User]):
    """
    관리자용 회원 목록 조회 API
    """

    queryset = User.objects.select_related("withdrawals").all().order_by("uuid")
    serializer_class = UserAdminListSerializer
    permission_classes = [IsAdminUser]

    # 페이지네이션, 필터링, 검색, 정렬 기능 구현
    pagination_class = UserAdminPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # UserFilter를 필터 클래스로 지정
    filterset_class = UserFilter
    # 검색 필드 지정
    search_fields = ["nickname", "name", "email"]
    # 정렬 필드 지정
    ordering_fields = ["uuid", "created_at", "name", "email"]
