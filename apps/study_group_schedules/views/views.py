from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_group_schedules.serializers import (
    StudyGroupScheduleCreateSerializer,
    StudyGroupScheduleResponseSerializerWithUUID,
)


@extend_schema(
    request=StudyGroupScheduleCreateSerializer,
    responses={201: StudyGroupScheduleResponseSerializerWithUUID},
    summary="스터디 그룹 스케줄 생성",
    description="새로운 스터디 그룹 스케줄을 생성합니다.",
    tags=["Study Group Schedules"],
)
class StudyGroupScheduleCreateView(APIView):
    """
    스터디 그룹 스케줄 생성
    """

    def post(self, request: Request) -> Response:
        serializer = StudyGroupScheduleCreateSerializer(data=request.data)

        if serializer.is_valid():
            schedule = serializer.save()
            response_serializer = StudyGroupScheduleResponseSerializerWithUUID(schedule)

            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
