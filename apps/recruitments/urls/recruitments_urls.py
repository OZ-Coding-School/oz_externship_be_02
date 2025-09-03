from django.contrib import path, include

urlpatterns = [
    path("api/v1/recruitments/", include("apps.recruitments.urls")),
]