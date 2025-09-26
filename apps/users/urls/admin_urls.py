from django.urls import URLPattern, URLResolver, include, path
from rest_framework.routers import DefaultRouter

from apps.users.views.admin_dashboard_view import (
    SignUpTrendAPIView,
    WithdrawalTrendAPIView,
)
from apps.users.views.admin_views import UserAdminViewSet, UserPermissionUpdateAPIView
from apps.users.views.admin_withdrawal_view import WithdrawalAdminViewSet

app_name = "admin_user"

router = DefaultRouter()

router.register("users", UserAdminViewSet, basename="users")
router.register("withdrawals", WithdrawalAdminViewSet, basename="admin-withdrawal")

urlpatterns: list[URLPattern | URLResolver] = [
    path("dashboard/signup-trends/", SignUpTrendAPIView.as_view(), name="dashboard-signup-trends"),
    path("dashboard/withdrawal-trends/", WithdrawalTrendAPIView.as_view(), name="dashboard-withdrawal-trends"),
    path("users/<uuid:user_uuid>/permission/", UserPermissionUpdateAPIView.as_view(), name="user_permissions"),
    path("", include(router.urls)),
]
