from typing import Any

from rest_framework import serializers

from apps.applications.models import Application


class ApplicationCreateSerializer(serializers.ModelSerializer[Application]):
    """
    - ModelSerializer를 상속받아 Application 모델과 연동됩니다.
    - 클라이언트로부터 받은 데이터의 유효성을 검증하고, Python 객체로 변환하는 역할을 한다.
    """

    class Meta:
        model = Application
        fields = [
            "self_introduction",
            "motivation",
            "objective",
            "available_time",
            "has_study_experience",
            "study_experience",
        ]

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        if data.get("has_study_experience") and not data.get("study_experience"):
            raise serializers.ValidationError(
                {"study_experience": "스터디 경험이 있다고 응답한 경우, 구체적인 경험을 필수로 입력해야 합니다."}
            )
        return data


# extend_schema에 사용하기 위한 응답용 Serializer
class ApplicationCreateResponseSerializer(serializers.Serializer[dict[str, Any]]):
    application_id = serializers.IntegerField()
    message = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer[dict[str, Any]]):
    error = serializers.CharField()
