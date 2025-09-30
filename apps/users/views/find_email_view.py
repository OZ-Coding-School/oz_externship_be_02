# apps/users/views/find_email_view.py

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.find_email_serializer import PhoneVerificationCodeSerializer
from apps.users.services.find_email_service import (
    FindEmailPhoneVerificationService,
    FindEmailService,
)
from apps.users.services.phone_service import (
    PhoneVerificationCodeFailedError,  # type: ignore
)
from apps.users.utils.enums import VerificationPurpose


class FindEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = PhoneVerificationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        purpose = VerificationPurpose.FIND_EMAIL

        try:
            # 인증 코드 검증: phone_number, code만 전달
            FindEmailPhoneVerificationService.verify_code(
                phone_number=serializer.validated_data["phone_number"],
                verification_code=serializer.validated_data["code"],
                purpose=purpose,
            )

            # 이메일 조회: name + phone_number 전달
            email = FindEmailService.find_email(
                name=serializer.validated_data["name"],
                phone_number=serializer.validated_data["phone_number"],
            )

        except PhoneVerificationCodeFailedError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response({"email": email}, status=status.HTTP_200_OK)
