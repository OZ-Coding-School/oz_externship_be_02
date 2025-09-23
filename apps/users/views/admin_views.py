from typing import Type, Union
from uuid import UUID

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, serializers, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.filters import UserFilter
from apps.users.models import User
from apps.users.permissions import IsSuperUser
from apps.users.serializers.admin_serializers import (
    UserAdminDetailSerializer,
    UserAdminListSerializer,
    UserAdminUpdateSerializer,
    UserPermissionResponseSerializer,
    UserPermissionUpdateSerializer,
)


@extend_schema(
    tags=["회원 관리 페이지 API - 회원 권한"],
    summary="회원 권한 수정",
    description="관리자 권한 유저(Superuser)가 특정 회원의 권한을 수정합니다.",
)
# 클래스 이름을 Update 기능에 집중하도록 변경 (선택사항이지만 권장)
class UserPermissionUpdateAPIView(APIView):
    # 이 API는 관리자(is_staff=True)만 접근 가능합니다.
    permission_classes = [IsSuperUser]

    @extend_schema(
        request=UserPermissionUpdateSerializer,
        responses={200: UserPermissionResponseSerializer},
    )
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


@extend_schema_view(
    list=extend_schema(
        tags=["관리자 페이지 API -회원 관리"],
        summary="회원 목록 조회",
        description="페이지네이션, 필터링, 검색, 정렬 기능이 포함된 회원 목록을 조회합니다.",
    ),
    retrieve=extend_schema(
        tags=["관리자 페이지 API -회원 관리"],
        summary="회원 상세 정보 조회",
        description="특정 회원의 상세 정보를 조회합니다.",
    ),
    partial_update=extend_schema(
        tags=["관리자 페이지 API -회원 관리"],
        summary="회원 정보 수정",
        description="특정 회원의 정보를 수정합니다. (부분 수정)",
    ),
    destroy=extend_schema(
        tags=["관리자 페이지 API -회원 관리"],
        summary="회원 정보 수정",
        description="관리자 권한(Superuser)가 특정 회원의 정보를 삭제합니다.",
    ),
)
class UserAdminViewSet(viewsets.ModelViewSet[User]):
    """
    관리자용 회원 CRUD API
    목록 조회 / 정보 상세 조회 (GET)
    회원 정보 수정 (PATCH)
    회원 정보 삭제 (DELETE)
    """

    queryset = User.objects.select_related("withdrawals").all().order_by("uuid")
    lookup_field = "uuid"

    # 페이지네이션, 필터링, 검색, 정렬 기능 구현
    pagination_class = UserAdminPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # UserFilter를 필터 클래스로 지정
    filterset_class = UserFilter
    # 검색 필드 지정
    search_fields = ["nickname", "name", "email"]
    # 정렬 필드 지정
    ordering_fields = ["uuid", "created_at", "name", "email"]

    def get_permissions(self) -> list[BasePermission]:
        """요청에 따라 다른 권한을 적용합니다."""
        if self.action == "destroy":
            # 회원 정보 삭제는 관리자(superuser)만 가능하도록 권한 설정
            return [IsSuperUser()]
        # 그 외 조회, 상세조회, 수정은 스태프 권한 이상 가능하도록 설정
        return [IsAdminUser()]

    # 요청에 따라 목록 조회 or 정보 상세 조회 시리얼라이저 반환
    def get_serializer_class(
        self,
    ) -> Type[Union[UserAdminDetailSerializer, UserAdminListSerializer, UserAdminUpdateSerializer]]:
        if self.action in ["update", "partial_update"]:
            return UserAdminUpdateSerializer
        if self.action == "retrieve":
            return UserAdminDetailSerializer

        return UserAdminListSerializer
