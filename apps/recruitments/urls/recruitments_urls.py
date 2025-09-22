from django.urls import include, path

from apps.recruitments.views.attachments_views import RecruitmentFileView
from apps.recruitments.views.images_views import RecruitmentImageView
from apps.recruitments.views.recruitment_detail_views import RecruitmentDetailView
from apps.recruitments.views.recruitment_views import MyRecruitmentView, RecruitmentView

urlpatterns = [
    path("", RecruitmentView.as_view(), name="recruitment-list"),
    path("/me", MyRecruitmentView.as_view(), name="recruitment-mylist"),
    path("/<uuid:recruitment_uuid>/applications", include("apps.applications.urls.recruitments_uuid_urls")),
    path("/<uuid:recruitment_uuid>", RecruitmentDetailView.as_view(), name="recruitment-detail"),
    path("/attachments", RecruitmentFileView.as_view(), name="recruitment-attachments-upload"),
    path("/images", RecruitmentImageView.as_view(), name="recruitment-images-upload"),
]
