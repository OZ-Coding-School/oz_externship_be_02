from django.urls import path

# POST 처리를 위한 View
from ..views.application_views import ApplicationAPIView

# GET 처리를 위한 View
from ..views.applications_list_views import RecruitmentApplicationListView

urlpatterns = [
    # name="application-create"는 Django 내에서 이 URL 경로에 대한 별칭을 지정하는 것으로,
    # 나중에 reverse() 함수 등을 통해 이 이름으로 URL을 쉽게 찾을 수 있다.
    # POST /api/v1/recruitments/{uuid}/applications
    path("", ApplicationAPIView.as_view(), name="application-create"),
    # GET /api/v1/recruitments/{uuid}/applications/all
    path("/all", RecruitmentApplicationListView.as_view(), name="recruitment-application-list"),
]
