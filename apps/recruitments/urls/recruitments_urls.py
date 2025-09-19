from django.urls import include, path

from apps.recruitments.views.attachments_views import RecruitmentFileUploadView
from apps.recruitments.views.recruitments_views import RecruitmentDetailView
from apps.recruitments.views.views_list import RecruitmentView

urlpatterns = [
    path("", RecruitmentView.as_view(), name="recruitment-list"),
    path("/<uuid:recruitment_uuid>/applications", include("apps.applications.urls")),
    path("/<uuid:recruitment_uuid>", RecruitmentDetailView.as_view(), name="recruitment-detail"),
    # application - endpoint prefix로 인해 여기서 처리
    path("/files/upload", RecruitmentFileUploadView.as_view(), name="recruitment-file-upload")
]
