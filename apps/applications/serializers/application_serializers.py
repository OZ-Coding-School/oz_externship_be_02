from typing import Any

from rest_framework import serializers

from apps.applications.models import Application


class ApplicationCreateSerializer(serializers.ModelSerializer[Application]):
    """
    - ModelSerializer를 상속받아 Application 모델과 연동됩니다.
    - 클라이언트로부터 받은 데이터의 유효성을 검증하고, Python 객체로 변환하는 역할을 한다.
    """

    class Meta:
        # 이 Serializer가 Application 모델을 기반으로 동작하도록 설정한다.
        # ModelSerializer는 이 설정을 보고 필드를 자동으로 생성하고 기본 유효성 검사를 수행한다.
        model = Application
        # 클라이언트로부터 직접 입력받을 필드들을 명시한다.
        fields = [
            "self_introduction",
            "motivation",
            "objective",
            "available_time",
            "has_study_experience",
            "study_experience",
        ]

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        DRF의 기본 유효성 검사가 끝난 후 호출되는 커스텀 유효성 검사 메서드.
        필드 간의 연관 관계 등 복잡한 비즈니스 규칙을 이곳에 구현한다.
        """
        # '스터디 경험 있음'을 선택했지만, 경험 내용을 적지 않은 경우 에러를 발생시킴.
        if data.get("has_study_experience") and not data.get("study_experience"):
            # ValidationError를 발생시키면, is_valid()가 False를 반환하고
            # serializer.errors에 해당 오류 메시지를 발생시킴.
            raise serializers.ValidationError(
                {"study_experience": "스터디 경험이 있다고 응답한 경우, 구체적인 경험을 필수로 입력해야 합니다."}
            )
        # 유효성 검사를 통과하면, 검증된 데이터를 그대로 반환.
        return data
