from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("", include("apps.recruitments.urls.recruitments_urls")),
    path("", include("apps.recruitments.urls.tags_urls")),
]
