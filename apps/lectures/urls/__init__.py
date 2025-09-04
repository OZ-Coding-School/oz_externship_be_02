from django.urls import include, path

urlpatterns = [
    path("", include("apps.lectures.urls.v1_bookmarks")),
]
