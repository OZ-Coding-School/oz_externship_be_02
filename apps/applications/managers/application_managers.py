from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import IntegrityError, models

from apps.recruitments.models import Recruitment
from apps.users.models import User

if TYPE_CHECKING:
    from ..models import Application


class ApplicationManager(models.Manager["Application"]):
    """
    Application 모델에 대한 커스텀 비즈니스 로직을 정의하는 매니저.
    View와 같은 다른 계층에서 ORM 관련 로직을 분리하여 코드의 응집도와 재사용성을 높인다.
    """

    def create_application(
        self,
        user: User,
        recruitment: Recruitment,
        **validated_data: Any,
    ) -> Application:
        """
        '중복 지원 불가' 규칙을 적용하여 Application 객체를 생성한다.

        Args:
            user (User): 지원하는 사용자 객체
            recruitment (Recruitment): 지원 대상이 되는 공고 객체
            **validated_data: Serializer를 통해 유효성 검사를 마친 데이터

        Raises:
            IntegrityError: 동일한 사용자가 동일한 공고에 이미 지원했을 경우 발생

        Returns:
            Application: 성공적으로 생성된 Application 객체
        """
        # exists()를 사용하여 DB에 공고 지원 이력 데이터 존재 여부만 확인한다.
        # 실제 데이터를 가져오지 않으므로 get()이나 filter()보다 효율적이다.
        if self.filter(user=user, recruitment=recruitment).exists():
            # View에서 받아서 처리할 수 있도록, '데이터 무결성 위반'을 의미하는 IntegrityError를 발생시킨다.
            raise IntegrityError("이미 해당 공고에 지원한 이력이 있습니다.")

        # 모든 검증을 통과하면, 기본 create 메서드를 호출하여 객체를 생성하고 반환한다.
        application = self.create(user=user, recruitment=recruitment, **validated_data)
        return application
