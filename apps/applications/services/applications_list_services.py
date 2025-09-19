from uuid import UUID

from django.db.models.query import QuerySet

from apps.applications.models import Application


class ApplicationListService:
    def get_applications_for_recruitment(self, recruitment_uuid: UUID) -> QuerySet[Application]:
        """특정 공고에 대한 지원서 목록을 반환합니다."""
        return Application.list_objects.get_applications_for_recruitment(recruitment_uuid=recruitment_uuid)
