from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.applications.models import Application
from apps.recruitments.models import Recruitment
from apps.users.models import User


class IsApplicantOrRecruiter(BasePermission):
    """
    지원자 본인 또는 공고 작성자만 접근 가능
    """

    def has_object_permission(
        self,
        request: Request,
        view: APIView,
        obj: Application,
    ) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        is_applicant = obj.user == request.user
        is_recruiter = obj.recruitment is not None and obj.recruitment.author == request.user
        return is_applicant or is_recruiter

    @staticmethod
    def has_permission_for_user(user: User, obj: Application) -> bool:
        if not user.is_authenticated:
            return False
        is_applicant = obj.user == user
        is_recruiter = obj.recruitment is not None and obj.recruitment.author == user
        return is_applicant or is_recruiter

    @staticmethod
    def _is_recruiter(user: User, obj: Application) -> bool:
        if not user or not user.is_authenticated:
            return False
        return getattr(obj.recruitment, "author", None) == user


class IsRecruiterOnly(BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: Application) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        # obj.recruitment.author가 현재 사용자와 같으면 True
        return obj.recruitment is not None and obj.recruitment.author == request.user

    @staticmethod
    def has_permission_for_user(user: User, obj: Application) -> bool:
        if not user.is_authenticated:
            return False
        return obj.recruitment is not None and obj.recruitment.author == user
