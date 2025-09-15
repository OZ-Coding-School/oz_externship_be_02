from __future__ import annotations

from typing import TYPE_CHECKING, Any

from apps.applications.models import Application
from apps.recruitments.models import Recruitment
from apps.users.models import User

if TYPE_CHECKING:
    from ..models import Application


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

        # Manager를 통해 실제 DB 로직을 수행하고, 서비스는 그 흐름을 제어한다.
        application = Application.objects.create_application(user=user, recruitment=recruitment, **validated_data)
        return application
