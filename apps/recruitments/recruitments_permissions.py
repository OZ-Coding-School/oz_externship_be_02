from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.recruitments.models import Recruitment


class IsRecruitmentAuthor(permissions.BasePermission):
    """
    요청한 사용자가 해당 공고의 작성자인지 확인하는 권한
    - DRF의 check_object_permissions()에 의해 호출된다.
    """

    def has_object_permission(self, request: Request, view: APIView, obj: Recruitment) -> bool:
        # obj는 확인 대상인 recruitment 객체.
        return obj.author == request.user
