from typing import Union

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import NotFound

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

        is_applicant = application.user == user  # 지원자 본인인지
        is_recruiter = False
        if application.recruitment is not None:
            is_recruiter = application.recruitment.author == user  # 공고 작성자인지

        if not (is_applicant or is_recruiter):
            raise PermissionDenied("이 지원 내역을 조회할 권한이 없습니다.")
        return application
