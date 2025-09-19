from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.recruitments.models import Recruitment


class IsRecruitmentAuthor(permissions.BasePermission):
    """
    요청한 사용자가 해당 공고의 작성자인지 확인하는 권한
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        try:
            recruitment_uuid = view.kwargs.get("recruitment_uuid")
            recruitment = Recruitment.objects.get(uuid=recruitment_uuid)

        except Recruitment.DoesNotExist:
            return False  # 공고가 존재하지 않으면 권한 없음

        return recruitment.author == request.user
