from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.models import GroupMember, StudyGroup
from apps.studies.permissions import IsStudyGroupLeaderPermission
from apps.studies.serializers.study_group import StudyGroupLeaderDelegateSerializer


class StudyGroupLeaderDelegateView(APIView):
    """
    스터디 그룹 리더는 스터디 그룹원에게 리더를 위임할 수 있다.
    """

    permission_classes = [IsStudyGroupLeaderPermission]

    @extend_schema(
        summary="스터디 그룹 리더 위임 API",
        description="스터디 그룹 리더는 스터디 그룹원에게 리더를 위임할 수 있다.",
        tags=["Study Group"],
        request=StudyGroupLeaderDelegateSerializer,
        responses=StudyGroupLeaderDelegateSerializer,
    )
    def post(self, request: Request, group_uuid: UUID) -> Response:
        serializer = StudyGroupLeaderDelegateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_leader_id = serializer.validated_data["new_leader_id"]

        group = get_object_or_404(StudyGroup, uuid=group_uuid)
        self.check_object_permissions(request, group)

        try:
            new_leader = GroupMember.objects.get(study_group=group, user__uuid=new_leader_id)
        except GroupMember.DoesNotExist:
            return Response(
                {"error": "스터디 그룹원이 아닌 유저에게 리더 권한 위임을 할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            update = group.members.through.objects.filter(
                study_group=group.id, user=new_leader.user, is_leader=False
            ).update(is_leader=True)
            if update:
                group.members.through.objects.filter(study_group=group.id, is_leader=True).exclude(
                    user=new_leader.user
                ).update(is_leader=False)
            return Response(status=status.HTTP_200_OK)
