from typing import Optional
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
from apps.users.models import User


@extend_schema(
    tags=["스터디 기록 (StudyNotes)"],
    summary="스터디 기록 생성",
    description="스터디 그룹에 속한 사용자가 학습 기록을 작성합니다.",
    request=StudyNoteSerializer,
    responses={
        201: StudyNoteSerializer,
        400: "잘못된 요청입니다. 필수 필드가 누락되었거나 형식이 올바르지 않습니다.",
        404: "해당 스터디 그룹을 찾을 수 없습니다.",
    },
)
class StudyNoteCreateView(APIView):
    permission_classes = [IsAuthenticated]
    service_class = StudyNoteService

    def get_service(self) -> Optional[StudyNoteService]:
        # 테스트 시 Mock을 주입할 수 있는 곳
        return self.service_class(s3_uploader=getattr(self, "s3_uploader", None))

    def post(self, request: Request, group_uuid: UUID) -> Response:
        group = get_object_or_404(StudyGroup, uuid=group_uuid)
        data = request.data.copy()
        serializer = StudyNoteSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        images = request.FILES.getlist("images")
        attachments = request.FILES.getlist("attachments")

        service = self.get_service() or self.service_class()

        assert isinstance(request.user, User)

        study_note = service.create_study_note(
            author=request.user,
            study_group=group,
            title=serializer.validated_data["title"],
            content=serializer.validated_data["content"],
            images=images,
            attachments=attachments,
        )

        return Response(StudyNoteSerializer(study_note).data, status=status.HTTP_201_CREATED)
