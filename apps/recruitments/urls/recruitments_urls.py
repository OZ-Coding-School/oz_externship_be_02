from django.urls import path

from ..views.views_list import RecruitmentListView

urlpatterns = [path("", RecruitmentListView.as_view(), name="recruitment-list")]
