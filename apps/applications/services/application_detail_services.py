from typing import Union

from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.applications.applications_permissions import IsApplicantOrRecruiter
from apps.applications.models import Application
from apps.users.models import User


class ApplicationDetailService:
    @staticmethod
    def get_application_detail(application_id: int, user: Union[User, AnonymousUser]) -> Application:
        # 함수 내의 모든 로직 들여쓰기
        try:
            application = Application.objects.select_related("user", "recruitment__author").get(id=application_id)
        except Application.DoesNotExist:
            raise NotFound("해당 지원 내역을 찾을 수 없습니다.")

        if isinstance(user, AnonymousUser):
            raise PermissionDenied("접근 권한이 없습니다.")

        permission = IsApplicantOrRecruiter
        if not permission.has_permission_for_user(user, application):
            raise PermissionDenied("접근 권한이 없습니다.")

        return application
