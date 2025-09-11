from django.urls import path

from ..application_views import ApplicationAPIView

urlpatterns = [
    # name="application-create"는 Django 내에서 이 URL 경로에 대한 별칭을 지정하는 것으로,
    # 나중에 reverse() 함수 등을 통해 이 이름으로 URL을 쉽게 찾을 수 있다.
    path("/recruitments/<uuid:recruitment_uuid>/applications", ApplicationAPIView.as_view(), name="application-create"),
]
