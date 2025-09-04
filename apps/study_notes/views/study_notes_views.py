from uuid import UUID

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.studies.models import StudyGroup
from apps.study_notes.serializers.study_notes_serializers import StudyNoteSerializer
from apps.study_notes.services.study_notes_services import StudyNoteService


class StudyNoteCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["StudyNotes"],
        summary="스터디 기록 생성",
        description="스터디 그룹에 속한 사용자가 스터디 기록을 생성합니다.",
        request=StudyNoteSerializer,
        responses=StudyNoteSerializer,
    )
    def post(self, request: Request, group_uuid: UUID) -> Response:
        assert request.user.is_authenticated
        group = get_object_or_404(StudyGroup, uuid=group_uuid)
        serializer = StudyNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # service에서 생성
        study_note = StudyNoteService().create_study_note(
            author=request.user,
            study_group=group,
            title=serializer.validated_data["title"],
            content=serializer.validated_data["content"],
            # images와 attachments는 비어있을 수도 있어서 get으로 가져옴
            images=serializer.validated_data.get("images"),
            attachments=serializer.validated_data.get("attachments"),
        )

        return Response(StudyNoteSerializer(study_note).data, status=status.HTTP_201_CREATED)
