from django.urls import path

from apps.studies.views.leader_delegate_view import StudyGroupLeaderDelegateView
from apps.studies.views.study_group_create_view import CreateStudyGroupView
from apps.studies.views.study_group_update_view import UpdateStudyGroupView

urlpatterns = [
    path("", CreateStudyGroupView.as_view(), name="create_study_group"),
    path("/<uuid:group_uuid>", UpdateStudyGroupView.as_view(), name="update_study_group"),
    path("/<uuid:group_uuid>/delegate", StudyGroupLeaderDelegateView.as_view(), name="leader_delegate"),
]
