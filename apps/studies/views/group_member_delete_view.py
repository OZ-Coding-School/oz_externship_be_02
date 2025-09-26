from typing import cast

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.models import StudyGroup
from apps.studies.permissions import IsStudyGroupMemberPermission
from apps.studies.services.delete_member_service import DeleteMemberService
from apps.users.models import User


class WithdrawGroupMemberView(APIView):
    """
    스터디 그룹원이 그룹 탈퇴 요청시 처리 로직
    """

    permission_classes = [IsStudyGroupMemberPermission]

    @extend_schema(
        summary="스터디 그룹 탈퇴 API",
        description="스터디 그룹의 모든 멤버들은 스터디 그룹에서 탈퇴할 수 있습니다.",
        tags=["Study Group"],
    )
    def delete(self, request: Request, group_uuid: str) -> Response:
        group = get_object_or_404(StudyGroup, uuid=group_uuid)
        self.check_object_permissions(request, group)
        user = cast(User, request.user)
        delete_member = DeleteMemberService(group=group, user=user)
        delete_member.studygroup_withdraw_service()
        return Response(status=status.HTTP_204_NO_CONTENT)
