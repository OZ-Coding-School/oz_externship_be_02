import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.serializers.study_group import StudyGroupCreateUpdateSerializer

logger = logging.getLogger(__name__)


class CreateStudyGroupView(APIView):
    """
    스터디 그룹 생성 APIView
    """

    parser_classes = [MultiPartParser]

    @extend_schema(
        summary="스터디 그룹 생성 API",
        description="모든 로그인 유저는 스터디 그룹 메뉴에 접속하여 스터디 그룹을 생성할 수 있습니다.",
        request=StudyGroupCreateUpdateSerializer,
        tags=["Study Group"],
        responses=StudyGroupCreateUpdateSerializer,
    )
    def post(self, request: Request) -> Response:
        serializer = StudyGroupCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 저장과 동시에 객체화
        serializer.save(user=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
