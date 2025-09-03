from typing import List

from django.urls import URLPattern, path

from apps.notifications import views

urlpatterns: List[URLPattern] = [
    # GET /api/v1/notifications
    path("", views.NotificationListView.as_view(), name="notification-list"),
    # PATCH /api/v1/notifications/<notification_id>
    path(
        "<int:notification_id>",
        views.NotificationUpdateView.as_view(),
        name="notification-update",
    ),
    # POST /api/v1/notifications/read-all
    path("read-all", views.NotificationReadAllView.as_view(), name="notification-read-all"),
    # GET /api/v1/notifications/unread-count
    path("unread-count", views.UnreadCountView.as_view(), name="notification-unread-count"),
]
