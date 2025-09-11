from django.urls import path

from apps.study_notes.views.study_notes_views import StudyNoteCreateView

urlpatterns = [
    # Post /api/v1/study-notes/<group_uuid> - 스터디 기록 생성
    path("/<uuid:group_uuid>/notes", StudyNoteCreateView.as_view(), name="create-study-note"),
]
