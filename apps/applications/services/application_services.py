from __future__ import annotations

from typing import Any

from django.db import IntegrityError

from apps.applications.models import Application
from apps.recruitments.models import Recruitment
from apps.users.models import User


class ApplicationService:
    """
    지원서 생성 및 관리를 담당하는 서비스 클래스
    """

    def create_application(
        self,
        user: User,
        recruitment: Recruitment,
        **validated_data: Any,
    ) -> Application:

        application = Application.objects.create_application(user=user, recruitment=recruitment, **validated_data)
        return application
