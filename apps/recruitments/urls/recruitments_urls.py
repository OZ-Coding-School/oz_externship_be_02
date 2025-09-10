from django.urls import path

from apps.recruitments.views.recruitments_views import RecruitmentDetailView
from apps.recruitments.views.views_list import RecruitmentView

urlpatterns = [
    path("", RecruitmentView.as_view(), name="recruitment-list"),
    path("/<uuid:recruitment_uuid>", RecruitmentDetailView.as_view(), name="recruitment-detail"),
]
