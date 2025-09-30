from django.urls import URLPattern, URLResolver, path

from apps.users.views.find_email_view import FindEmailView
from apps.users.views.user_info_view import UserInfoEditView, UserInfoView

urlpatterns: list[URLPattern | URLResolver] = [
    path("info/", UserInfoView.as_view(), name="user_info"),
    path("info/edit/", UserInfoEditView.as_view(), name="user_info_edit"),
    path("info/find-email/", FindEmailView.as_view(), name="find_email"),
]
