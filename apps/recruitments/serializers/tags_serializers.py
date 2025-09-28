# recruitments 앱에서 사용되는 Tag 모델에 대한 Serializer를 정의한다.
from typing import Any, ClassVar, Dict, List

from profanity_check import predict
from rest_framework import serializers

from apps.recruitments.badwords import PROFANITY_WORD_LIST
from apps.recruitments.models.tags import Tag


class TagSerializer(serializers.ModelSerializer[Tag]):

    class Meta:
        model = Tag
        fields = ["id", "name"]
        # id와 name 필드를 클라이언트에게 반환하고, 데이터 유효성 검사를 수행한다.
        # unique=True에 의한 UniqueValidator와 max_length 검사가 자동으로 활성화된다.

    def validate_name(self, value: str) -> str:
        """
        태그 이름에 욕설이나 비속어가 포함되어 있는지 2단계로 검증한다.
        1. badwords.py의 단어 목록과 비교 (규칙 기반)
        2. alt-profanity-check 라이브러리로 2차 검증 (모델 기반)
        """
        # 1단계: 규칙 기반 필터
        for profanity in PROFANITY_WORD_LIST:
            if profanity.lower() in value.lower():
                raise serializers.ValidationError("태그에 욕설이나 비속어를 포함할 수 없습니다.")

        # 2단계: 모델 기반 필터
        is_profane = predict([value])[0]
        if is_profane:
            raise serializers.ValidationError("태그에 욕설이나 비속어를 포함할 수 없습니다.")

        return value
