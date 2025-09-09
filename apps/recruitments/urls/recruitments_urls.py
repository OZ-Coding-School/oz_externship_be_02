from django.urls import path

from apps.recruitments.views.recruitments_views import RecruitmentDetailView

urlpatterns = [
    path("/<uuid:recruitment_uuid>", RecruitmentDetailView.as_view(), name="recruitment-detail"),
]
