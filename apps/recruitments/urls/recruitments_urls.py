from django.urls import URLPattern, URLResolver, path

from apps.recruitments.views.recruitments_views import RecruitmentDetailView
from apps.recruitments.views.views_list import RecruitmentView

urlpatterns: list[URLPattern | URLResolver] = [
    path("", RecruitmentView.as_view(), name="recruitment-list"),
    path("/<uuid:recruitment_uuid>", RecruitmentDetailView.as_view(), name="recruitment-detail"),
]
