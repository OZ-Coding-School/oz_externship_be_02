from django.urls import include, path

from ..views.tags_views import TagAPIView

app_name = "recruitments"

urlpatterns = [
    path("", include("apps.recruitments.urls.recruitments_urls")),
    path("/tags", include("apps.recruitments.urls.tags_urls")),
]
