from django.urls import path

from ..views.views_list import RecruitmentView

urlpatterns = [
    path("", RecruitmentView.as_view(), name="recruitment")
]