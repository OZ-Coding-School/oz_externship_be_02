from django.urls import URLPattern, URLResolver, path

from apps.users.views.admin_views import UserPermissionAPIView

app_name = "admin_user"

urlpatterns: list[URLPattern | URLResolver] = [
    path("/<uuid:user_uuid>", UserPermissionAPIView.as_view(), name="user_permissions"),
]
