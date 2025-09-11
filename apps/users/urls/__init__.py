from django.urls import URLPattern, URLResolver, include, path

urlpatterns: list[URLPattern | URLResolver] = [
    path("auth", include("apps.users.urls.auth_urls")),
    path("users", include("apps.users.urls.users_urls")),
]
