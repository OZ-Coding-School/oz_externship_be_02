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

        # 서비스 계층에서 중복 지원 여부를 먼저 확인한다.
        if Application.objects.has_applied(user=user, recruitment=recruitment):
            raise IntegrityError("이미 해당 공고에 지원한 이력이 있습니다.")

        # 중복이 아닐 경우, Manager의 생성 메서드를 호출한다.
        application = Application.objects.create_application(user=user, recruitment=recruitment, **validated_data)
        return application
