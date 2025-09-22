from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from django.db import models

from apps.recruitments.models import Recruitment
from apps.users.models import User

if TYPE_CHECKING:  # pragma: no cover
    from ..models import Application


class ApplicationManager(models.Manager["Application"]):
    def get_applications_for_recruitment(self, recruitment_uuid: UUID) -> models.QuerySet["Application"]:
        """특정 공고에 대한 지원서 목록을 반환하는 매니저 메소드"""
        return self.filter(recruitment__uuid=recruitment_uuid).select_related("user")

    def has_applied(self, user: User, recruitment: Recruitment) -> bool:
        """
        사용자가 특정 공고에 이미 지원했는지 확인한다.

        Args:
            user (User): 확인할 사용자 객체
            recruitment (Recruitment): 확인할 공고 객체

        Returns:
            bool: 지원 이력이 있으면 True, 없으면 False
        """
        return self.filter(user=user, recruitment=recruitment).exists()

    def create_application(
        self,
        user: User,
        recruitment: Recruitment,
        **validated_data: Any,
    ) -> Application:
        """
        Application 객체를 생성한다. (사전 조건: 중복 지원 검사는 이미 완료되어야 함)

        Args:
            user (User): 지원하는 사용자 객체
            recruitment (Recruitment): 지원 대상이 되는 공고 객체
            **validated_data: Serializer를 통해 유효성 검사를 마친 데이터

        Returns:
            Application: 성공적으로 생성된 Application 객체
        """
        # 생성 로직만 남긴다.
        application = self.create(user=user, recruitment=recruitment, **validated_data)
        return application
