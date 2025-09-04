from django.urls import path

from apps.recruitments.views.recruitments_views import RecruitmentDetailView

urlpatterns = [
    path("<int:recruitmentId>/", RecruitmentDetailView.as_view(), name="recruitment-detail"),
]
