from typing import Any
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist

from apps.recruitments.serializers.recruitments_serializers import (
    RecruitmentUpdateSerializer,
)

from ..models.recruitments import Recruitment


def get_recruitment_detail(recruitment_uuid: UUID) -> Recruitment:
    try:
        recruitment = (
            Recruitment.objects.select_related("author")
            .prefetch_related("tags", "attachments", "bookmark_users")
            .get(uuid=recruitment_uuid)
        )
        return recruitment
    except Recruitment.DoesNotExist:
        raise ObjectDoesNotExist("해당 공고를 찾을 수 없음.")


# 주어진 공고 객체를 전달받은 데이터로 수정
def update_recruitment(recruitment: Recruitment, data: dict[str, Any]) -> Recruitment:
    serializer = RecruitmentUpdateSerializer(instance=recruitment, data=data, partial=True)
    serializer.is_valid(raise_exception=True)
    updated_recruitment = serializer.save()
    return updated_recruitment
