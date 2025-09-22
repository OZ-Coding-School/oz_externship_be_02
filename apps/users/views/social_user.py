from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.social_user import (
    KakaoLoginResponseSerializer,
    UserMinimalResponseSerializer,
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
                "user": UserMinimalResponseSerializer(user_instance).data,
            }

            serializer = KakaoLoginResponseSerializer(response_data)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except (ValidationError, DjangoValidationError) as e:
            return Response({"message": f"잘못된 요청: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        except APIException as e:
            detail_obj: Any = getattr(e, "detail", None)
            if isinstance(detail_obj, str):
                detail_str: str = detail_obj
            else:
                detail_str = str(detail_obj if detail_obj is not None else e)

            status_obj: Any = getattr(e, "status_code", None)
            status_code: int = status_obj if isinstance(status_obj, int) else status.HTTP_400_BAD_REQUEST

            return Response({"message": f"잘못된 요청: {detail_str}"}, status=status_code)

        except Exception:
            return Response({"message": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
