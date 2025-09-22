from django.urls import URLPattern, URLResolver, include, path

app_name = "lectures"

urlpatterns: list[URLPattern | URLResolver] = [
    path("", include("apps.lectures.urls.v1_bookmarks")),
]
