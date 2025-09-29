from typing import cast

from rest_framework.permissions import DjangoObjectPermissions
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.studies.models import StudyGroup
from apps.users.models import User


class IsMemberOnStudyGroup(DjangoObjectPermissions):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return True

    def has_object_permission(self, request: Request, view: APIView, obj: StudyGroup) -> bool:
        # 접근 권한 확인
        if not obj.groupmember_set.filter(user=cast(User, request.user)).exists():
            return False
        return True
