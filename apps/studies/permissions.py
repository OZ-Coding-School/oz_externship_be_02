from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.studies.models import GroupMember, StudyGroup


class IsStudyGroupLeaderPermission(permissions.BasePermission):
    """
    스터디 그룹 정보 수정 및 그룹원 강퇴 기능 등 리더 권한 여부 확인
    """

    def has_object_permission(
        self, request: Request, view: APIView, obj: Any
    ) -> Any:  # 특정 권한 객체에 대한 권한 확인
        """
        :param request: HTTP request
        :param view: view 인스턴스
        :param obj: StudyGroup 인스턴스
        :return:
        """

        study_group = obj

        if not request.user.is_authenticated:
            return False

        # 리더 권한 확인
        return study_group.members.through.objects.filter(user=request.user, is_leader=True).exists()
