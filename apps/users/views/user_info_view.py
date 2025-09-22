# apps/users/views/user_info_view.py

from django.contrib.auth.models import AnonymousUser
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models.user import User
from apps.users.serializers.user_info_serializer import UserInfoSerializer
from apps.users.services.user_info_service import UserInfoEditService


class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        현재 로그인한 사용자의 정보를 반환(정보 조회).
        """
        assert not isinstance(request.user, AnonymousUser)
        user: User = request.user # mypy

        serializer = UserInfoSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request: Request) -> Response:
        """
        사용자 정보를 수정.
        변경 사항에 휴대폰 번호가 포함되어 있다면, service에서 인증 여부를 확인하고 캐시를 삭제.
        """
        # 오류: 비로그인 유저(401)
        if isinstance(request.user, AnonymousUser):
            return Response({"detail": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)
    
        try:
            assert not isinstance(request.user, AnonymousUser)
            user: User = request.user # mypy

            # 사용자 정보 수정 서비스 호출
            updated_user = UserInfoEditService(request.user).update_user_info(request.data)

            # 수정된 사용자 정보를 다시 직렬화하여 응답
            serializer = UserInfoSerializer(updated_user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValidationError as e:
            # 오류: 인증/유효성 검사 실패(400)
            print(f"인증에 실패하였습니다. {str(e)}.")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # 오류: 알 수 없는 오류(500)
            print(f"Unexpected error during user info update: {str(e)}")
            return Response({"detail": "알 수 없는 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)