# apps/users/views/find_email_view.py
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.find_email_serializer import PhoneVerificationCodeSerializer
from apps.users.services.phone_service import PhoneVerificationService
from apps.users.utils.enums import VerificationPurpose


class FindEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        data = request.data

        # 2. 인증번호 검증 + 이메일 조회 단계
        serializer = PhoneVerificationCodeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        if not PhoneVerificationService.is_verified(
            purpose=VerificationPurpose.FIND_EMAIL,
            verification_code=serializer.validated_data["code"],
            phone_number=serializer.validated_data["phone_number"],
        ):
            raise AuthenticationFailed("인증정보가 일치하지 않습니다.")

        try:
            user = User.objects.get(
                name=serializer.validated_data["name"], phone_number=serializer.validated_data["phone_number"]
            )
        except User.DoesNotExist:
            # 404 처리용 예외
            raise NotFound("입력하신 이름과 휴대폰 번호로 등록된 사용자를 찾을 수 없습니다.")

        return Response({"email": user.email}, status=status.HTTP_200_OK)
