# apps/users/views/user_info_view.py

from typing import cast

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models.user import User
from apps.users.services.user_info_service import (
    UserInfoEditService,
    UserInfoService,
)

# 로그인한 사용자만 접근할 수 있는 APIView 기본 클래스: permission_classes를 IsAuthenticated로 고정
class AuthenticatedAPIview(APIView):
    permission_classes = [IsAuthenticated]

class UserInfoView(AuthenticatedAPIview):
    def get(self, request: Request) -> Response:
        """
        자신(로그인한 사용자)의 정보 조회.
        """
        service = UserInfoService(cast(User, request.user))
        data = service.get_user_info()

        return Response(data, status=status.HTTP_200_OK)


class UserInfoEditView(AuthenticatedAPIview):
    def patch(self, request: Request) -> Response:
        """
        현재 로그인한 사용자의 정보를 수정하는 API 뷰.
        로그인 필수. 휴대폰 번호 변경 시 인증 코드 검증 포함.
        """ 
        # 로그인한 사용자를 기반으로 서비스 인스턴스 생성
        service = UserInfoEditService(cast(User, request.user))

        try: # 사용자 정보 업데이트
            service.update_user_info(request.data)
        except ValidationError as e: # ValidationError의 종류가 달라도 안전하게 Response를 반환
            detail = getattr(e, "detail", str(e))
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "회원 정보가 성공적으로 수정되었습니다."}, status=status.HTTP_200_OK)
