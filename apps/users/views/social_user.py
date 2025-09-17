from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.social_user import (
    KakaoLoginResponseSerializer,
    UserResponseSerializer,
)
from apps.users.services.social_user import KakaoService


class KakaoLoginCallbackView(APIView):
    def get(self, request: Request) -> Response:
        code: str | None = request.query_params.get("code")
        if not code:
            return Response(
                {"message": "code is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = KakaoService()

        try:
            result = service.kakao_login(code)

            user_instance = result["user"]
            response_data = {
                "message": result["message"],
                "access": result["access"],
                "refresh": result["refresh"],
                "is_new_user": result["is_new_user"],
                "user": UserResponseSerializer(user_instance).data,
            }

            serializer = KakaoLoginResponseSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"message": f"잘못된 요청: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
