from typing import TYPE_CHECKING
from uuid import UUID

from django.db import models

if TYPE_CHECKING:  # pragma: no cover
    from apps.applications.models import Application


class ApplicationListManager(models.Manager["Application"]):
    def get_applications_for_recruitment(self, recruitment_uuid: UUID) -> models.QuerySet["Application"]:
        """특정 공고에 대한 지원서 목록을 반환하는 매니저 메소드"""
        return self.filter(recruitment__uuid=recruitment_uuid).select_related("user")
