from django.urls import path, include

from apps.applications.application_views import ApplicationAPIView
from apps.recruitments.views.recruitments_views import RecruitmentDetailView
from apps.recruitments.views.views_list import RecruitmentView

urlpatterns = [
    path("", RecruitmentView.as_view(), name="recruitment-list"),
    path("/<uuid:recruitment_uuid>", RecruitmentDetailView.as_view(), name="recruitment-detail"),

    # application - endpoint prefix로 인해 여기서 처리
    path("/<uuid:recruitment_uuid>/applications", include("apps.applications.urls.recruitments_uuid_urls")),
]
