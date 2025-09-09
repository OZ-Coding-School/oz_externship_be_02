import logging

from django.core.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.models import GroupMember
from apps.studies.serializers.study_group import (
    CreateSuccessResponse,
    StudyGroupLeaderSerializer,
    StudyGroupSerializer,
)
from apps.users.models.user import User

logger = logging.getLogger(__name__)


class CreateStudyGroupView(APIView):
    """
    스터디 그룹 생성 APIView"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="스터디 그룹 생성 API",
        description="모든 로그인 유저는 스터디 그룹 메뉴에 접속하여 스터디 그룹을 생성할 수 있습니다.",
        request=StudyGroupSerializer,
        tags=["Study Group"],
    )
    def post(self, request: Request) -> Response:
        serializer = StudyGroupSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # 저장과 동시에 객체화
        study_group = serializer.save()

        # 로그인 여부 확인
        if not request.user.is_authenticated:
            raise PermissionDenied("로그인이 필요합니다.")

            # 리더 데이터 가져오기
        leader = GroupMember.objects.get(study_group=study_group, user=request.user)
        leader_ = StudyGroupLeaderSerializer(leader.user)

        # 응답 데이터
        response_data = {
            "uuid": study_group.uuid,
            "name": study_group.name,
            "introduction": study_group.introduction,
            "profile_img_url": study_group.profile_img_url,
            "start_at": study_group.start_at,
            "end_at": study_group.end_at,
            "max_headcount": study_group.max_headcount,
            "created_by": leader_.data,
            "created_at": study_group.created_at,
        }
        success_response = CreateSuccessResponse(data=response_data)
        if success_response.is_valid():
            print(success_response.data)
            return Response(success_response.data, status=status.HTTP_201_CREATED)
        else:
            return Response(success_response.errors, status=status.HTTP_400_BAD_REQUEST)
