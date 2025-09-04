# apps/users/views/withdrawals.py

from datetime import date, timedelta

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.withdrawals import (
    WithdrawalRequestSerializer,
    WithdrawalSerializer,
)


# 로그인한 사용자만 접근 가능
class WithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        # 1) 비밀번호 확인: 입력 데이터의 유효성 검증, 올바른 타입인지 체크
        #    { "password": "strongPassword123!" } 같은 식
        pw_serializer = WithdrawalRequestSerializer(data=request.data)
        pw_serializer.is_valid(raise_exception=True)

        # 1-1) 비밀번호가 틀렸다면: HTTP 400 반환
        if not request.user.check_password(pw_serializer.validated_data["password"]):
            return Response({"error": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        # 2) 탈퇴 기록을 DB에 저장: 신청 데이터의 유효성 검증
        #    save() 호출 시 user와 due_date를 외부에서 전달
        #    따라서 create() 내부에 request.user를 넣을 필요가 사라짐
        withdrawal_serializer = WithdrawalSerializer(data=request.data)
        withdrawal_serializer.is_valid(raise_exception=True)
        withdrawal_serializer.save(user=request.user, due_date=date.today() + timedelta(days=14))

        # 2-1) 유효하다면: HTTP 200 반환
        return Response(
            {"message": "Account withdrawal requested successfully. Your account will be deleted after 2 weeks."},
            status=status.HTTP_200_OK,
        )
