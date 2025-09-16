from django.urls import path

from apps.studies.views.study_group_create_view import CreateStudyGroupView

urlpatterns = [
    path("", CreateStudyGroupView.as_view(), name="create_study_group"),
]
