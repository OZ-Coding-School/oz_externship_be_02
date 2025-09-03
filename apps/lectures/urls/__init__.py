from django.urls import include, path

urlpatterns = [
    path("v1/", include("apps.lectures.urls.v1_bookmarks")),
]
