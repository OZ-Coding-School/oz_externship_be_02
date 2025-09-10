from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("users", include("apps.users.urls.admin_urls")),
]
