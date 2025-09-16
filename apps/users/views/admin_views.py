from uuid import UUID

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.permissons import IsSuperUser
from apps.users.serializers.admin_serializers import (
    UserPermissionRequestSerializer,
    UserPermissionResponseSerializer,
)
from apps.users.services.admin_servies import UserPermissionService


# 클래스 이름을 Update 기능에 집중하도록 변경 (선택사항이지만 권장)
class UserPermissionUpdateAPIView(APIView):
    # 이 API는 관리자(is_staff=True)만 접근 가능합니다.
    permission_classes = [IsSuperUser]

    def patch(self, request: Request, user_uuid: UUID) -> Response:
        # 1. 권한 변경 대상 유저 찾기
        target_user = get_object_or_404(User, uuid=user_uuid)

        # 2. Request 시리얼라이저로 데이터 유효성 검사
        request_serializer = UserPermissionRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        # 3. 유효성 검사를 통과한 데이터를 서비스에 전달
        permission = request_serializer.validated_data["permission"]
        update_user = UserPermissionService.update_user_permission(user=target_user, permission=permission)

        # 3. Response 시리얼라이저로 응답데이터 형성
        response_serializer = UserPermissionResponseSerializer(updated_user)
        return Response(
            {"detail": "권한이 성공적으로 변경되었습니다.", "data": response_serializer.data},
            status=status.HTTP_200_OK,
        )
