from django.urls import URLPattern, URLResolver, path

from apps.users.views.user_info_view import UserInfoView

urlpatterns: list[URLPattern | URLResolver] = [
    path("info/", UserInfoView.as_view(), name="user_info"),
]