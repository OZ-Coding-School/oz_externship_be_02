# apps/users/serializers/withdrawals.py

from datetime import date, timedelta

from rest_framework import serializers

from apps.users.models.withdrawals import WithdrawalsReasonChoices, Withdrwals

# 사용자 본인 인증 부분(비밀번호 검증)
class WithdrawalRequestSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

# DB에 기록되는 부분
class WithdrawalSerializer(serializers.ModelSerializer):
    # 사용자가 탈퇴 이유를 선택할 때, 이미 정의된 값만 고를 수 있도록 제한함(ChoiceField)
    reason = serializers.ChoiceField(choices=WithdrawalsReasonChoices.choices)
    # 사용자가 읽기 편하도록 한글 레이블을 제공(get_reason_display)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    # class Meta: 설정 정보를 담는 내부 클래스
    class Meta:
        model = Withdrwals
        fields = ["user", "reason", "reason_display" "reason_detail", "due_date"]
        # 아래는 사용자가 직접 선택하지 않는 부분
        #     user: 현재 로그인한 사용자만 해당
        #     reason_display: 응답 전용
        #     due_date: 서버에서 자동 계산
        read_only_fields = ["user", "reason_display", "due_date"]

    # 로그인된 사용자만 탈퇴할 수 있도록 user를 자동으로 할당 - create()를 오버라이드
    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user

        # 탈퇴 신청일에서 2주(14일) 뒤에 계정이 탈퇴(삭제)되도록 due_date 자동 설정
        validated_data["due_date"] = date.today() + timedelta(days=14)
        return super().create(validated_data)
