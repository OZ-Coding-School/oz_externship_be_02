from django.urls import URLPattern, URLResolver, include, path
from rest_framework.routers import DefaultRouter

from apps.users.views.admin_views import UserAdminViewSet, UserPermissionUpdateAPIView

app_name = "admin_user"

router = DefaultRouter()
router.register("", UserAdminViewSet, basename="users")

urlpatterns: list[URLPattern | URLResolver] = [
    path("users/<uuid:user_uuid>/permission", UserPermissionUpdateAPIView.as_view(), name="user_permissions"),
    path("", include(router.urls)),
]
