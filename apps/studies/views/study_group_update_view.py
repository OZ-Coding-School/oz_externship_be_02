import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.models import StudyGroup
from apps.studies.permissions import IsStudyGroupLeaderPermission
from apps.studies.serializers.study_group import StudyGroupCreateUpdateSerializer

logger = logging.getLogger(__name__)


class UpdateStudyGroupView(APIView):
    """
    스터디 그룹 정보 수정 APIView
    """

    permission_classes = [IsStudyGroupLeaderPermission]

    @extend_schema(
        summary="스터디 그룹 정보 수정 API",
        description="스터디 그룹의 리더는 스터디 그룹 상세 조회 페이지 내에서 스터디 그룹 정보 수정페이지로 이동하여 그룹 정보를 수정할 수 있습니다.",
        request=StudyGroupCreateUpdateSerializer,
        tags=["Study Group"],
        responses=StudyGroupCreateUpdateSerializer,
    )
    def patch(self, request: Request, group_uuid: str) -> Response:
        study_group_data = get_object_or_404(StudyGroup, uuid=group_uuid)
        self.check_object_permissions(request, study_group_data)  # 스터디 그룹 리더 권한 여부 확인
        serializer = StudyGroupCreateUpdateSerializer(instance=study_group_data, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
