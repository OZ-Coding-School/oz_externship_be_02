from django.urls import path

from apps.study_notes.views.study_notes_upload_view import StudyNoteUploadView
from apps.study_notes.views.study_notes_views import StudyNoteCreateView

urlpatterns = [
    # Post /api/v1/study-notes/<group_uuid> - 스터디 기록 생성
    path("/<uuid:group_uuid>/notes", StudyNoteCreateView.as_view(), name="create-study-note"),
    # POST /api/v1/study-notes/<group_uuid>/upload - 이미지/첨부파일 업로드
    path("<uuid:group_uuid>/upload", StudyNoteUploadView.as_view(), name="upload-study-note-files"),
]
