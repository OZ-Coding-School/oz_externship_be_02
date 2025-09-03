from django.urls import include, path

urlpatterns = [path("auth/", include("apps.users.urls.auth_urls"))]
