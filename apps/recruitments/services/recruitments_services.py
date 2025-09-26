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


def get_recruitment_detail_for_admin(recruitment_id: int) -> Recruitment:
    try:
        recruitment = (
            Recruitment.admin_objects.select_related(
                "study_group",
                "author",
            )
            .prefetch_related(
                "tags", "attachments", "bookmark_users", "applications", "applications__user", "study_group__lectures"
            )
            .get(id=recruitment_id)
        )
        return recruitment
    except Recruitment.DoesNotExist:
        raise NotFound(f"ID {recruitment_id}에 해당하는 공고를 찾을 수 없습니다.")
