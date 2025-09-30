from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.find_email_serializer import PhoneVerificationCodeSerializer
from apps.users.services.find_email_service import FindEmailService
from apps.users.services.phone_service import PhoneVerificationService
from apps.users.utils.enums import VerificationPurpose


class FindEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["사용자"],
        summary="이메일 찾기",
        description="이름과 휴대폰 번호, 인증 코드를 통해 사용자의 이메일을 찾습니다.",
        request=PhoneVerificationCodeSerializer,
        responses={
            200: OpenApiResponse(
                description="이메일 조회 성공",
                examples=[
                    OpenApiExample(
                        "성공 응답 예시",
                        value={"email": "example@test.com"},
                    )
                ],
            ),
            400: OpenApiResponse(description="인증 코드 검증 실패"),
            404: OpenApiResponse(description="해당 조건에 맞는 이메일 없음"),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = PhoneVerificationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        purpose = VerificationPurpose.FIND_EMAIL

        # 인증 코드 검증: phone_number, code만 전달
        if not PhoneVerificationService.is_verified(
            phone_number=serializer.validated_data["phone_number"],
            verification_code=serializer.validated_data["code"],
            purpose=purpose,
        ):
            return Response("입력하신 인증정보가 유효하지 않습니다.", status.HTTP_400_BAD_REQUEST)

        # 이메일 조회: name + phone_number 전달
        email = FindEmailService.find_email(
            name=serializer.validated_data["name"],
            phone_number=serializer.validated_data["phone_number"],
        )

        return Response({"email": email}, status=status.HTTP_200_OK)
