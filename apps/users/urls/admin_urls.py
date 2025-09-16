from django.urls import URLPattern, URLResolver, path

from apps.users.views.admin_views import UserPermissionUpdateAPIView

app_name = "admin_user"

urlpatterns: list[URLPattern | URLResolver] = [
    path("/<uuid:user_uuid>/permission", UserPermissionUpdateAPIView.as_view(), name="user_permissions"),
]
