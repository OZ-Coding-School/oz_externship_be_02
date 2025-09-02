from jsonschema.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.user_serializer import (
    VerificationSerializer,
)
from apps.users.services.auth_service import (
    verify_user_email,
)


class VerificationView(APIView):
    def post(self, request):
        serializer = VerificationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                verify_user_email(
                    serializer.validated_data["email"],
                    serializer.validated_data["verification_code"],
                )
                return Response({"message": "이메일 인증 성공"}, status=status.HTTP_200_OK)
            except ValidationError as e:
                return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


