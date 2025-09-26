from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.study_notes.models import StudyNote


class IsStudyNoteAuthor(BasePermission):
    """
    스터디 노트 작성자만 접근 가능
    """

    def has_object_permission(self, request: Request, view: APIView, obj: StudyNote) -> bool:
        return obj.author_id == request.user.id
