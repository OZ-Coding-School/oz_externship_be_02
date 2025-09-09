from django.urls import path

from apps.studies.views.create_studygroup import CreateStudyGroupView

app_name = "studies"

urlpatterns = [
    path("/group", CreateStudyGroupView.as_view(), name="create_study_group"),
]
