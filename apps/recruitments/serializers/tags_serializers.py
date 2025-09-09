# recruitments 앱에서 사용되는 Tag 모델에 대한 Serializer를 정의한다.
from typing import Any, ClassVar, Dict, List

from rest_framework import serializers

from apps.recruitments.models.tags import Tag


class TagSerializer(serializers.ModelSerializer[Tag]):

    class Meta:
        model = Tag
        fields = ["id", "name"]
        # id와 name 필드를 클라이언트에게 반환하고, 데이터 유효성 검사를 수행한다.
        # unique=True에 의한 UniqueValidator와 max_length 검사가 자동으로 활성화된다.
