# apps/users/views/reset_password_view.py

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.reset_password_serializer import ResetPasswordSerializer


class ResetPasswordAPIView(APIView):
    # 인증 필요 없음
    authentication_classes = []  # 기본 인증 무시
    permission_classes = []  # 권한 무시

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={200: {"detail": "비밀번호가 성공적으로 변경되었습니다."}},
        description="비밀번호 재설정 API입니다. 이메일과 새 비밀번호를 입력하면 비밀번호가 변경됩니다.",
        tags=["Users"],
    )
    def post(self, request: Request) -> Response:
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # 입력 검증
        serializer.save()  # 비밀번호 변경
        return Response({"detail": "비밀번호가 성공적으로 변경되었습니다."}, status=status.HTTP_200_OK)
