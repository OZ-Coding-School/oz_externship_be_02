# recruitments 앱에서 사용되는 Tag 모델에 대한 Serializer를 정의한다.
from typing import Any, ClassVar, Dict, List
from rest_framework import serializers

from apps.recruitments.models.tags import Tag


class TagSerializer(serializers.ModelSerializer[Tag]):

    class Meta:
        model = Tag
        fields = ["id", "name"]  # id와 name 필드를 클라이언트에게 반환하고, 데이터 유효성 검사를 수행한다.
        # unique=True에 의해 자동으로 추가되는 UniqueValidator를 비활성화한다.
        # 중복 검사는 Service Layer에서 직접 처리할것 .
        extra_kwargs: ClassVar[Dict[str, Dict[str, List[Any]]]] = {
            "name": {"validators": []},
        }
