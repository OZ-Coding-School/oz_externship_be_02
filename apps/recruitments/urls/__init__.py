from django.urls import include, path

app_name = "recruitments"

urlpatterns = [
    path("", include("apps.recruitments.urls.tags_urls")),
]
