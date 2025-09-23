from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.applications.models import Application


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
