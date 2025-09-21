from uuid import UUID

from rest_framework.exceptions import NotFound

from ..models.recruitments import Recruitment


def get_recruitment_detail(recruitment_uuid: UUID) -> Recruitment:
    try:
        recruitment = (
            Recruitment.objects.select_related("author")
            .prefetch_related("tags", "attachments", "images")
            .get(uuid=recruitment_uuid)
        )
        return recruitment
    except Recruitment.DoesNotExist:
        raise NotFound("해당 공고를 찾을 수 없음.")


def delete_recruitment(recruitment: Recruitment) -> None:
    recruitment.delete()
