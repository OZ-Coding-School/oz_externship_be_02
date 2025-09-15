import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.serializers.study_group import (
    CreateSuccessResponse,
    StudyCreateSerializer,
    StudyGroupSerializer,
)

logger = logging.getLogger(__name__)


class CreateStudyGroupView(APIView):
    """
    스터디 그룹 생성 APIView
    """

    @extend_schema(
        summary="스터디 그룹 생성 API",
        description="모든 로그인 유저는 스터디 그룹 메뉴에 접속하여 스터디 그룹을 생성할 수 있습니다.",
        request=StudyGroupSerializer,
        tags=["Study Group"],
        responses=CreateSuccessResponse,
    )
    def post(self, request: Request) -> Response:
        input_data = {"study_group": request.data}
        serializer = StudyCreateSerializer(data=input_data)
        if serializer.is_valid():
            # 저장과 동시에 객체화
            data = serializer.save(user=self.request.user)
            response = CreateSuccessResponse(instance=data)
            return Response(response.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
