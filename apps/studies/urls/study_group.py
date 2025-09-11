from django.urls import path

from apps.studies.views.create_studygroup import CreateStudyGroupView

urlpatterns = [
    path("", CreateStudyGroupView.as_view(), name="create_study_group"),
]
