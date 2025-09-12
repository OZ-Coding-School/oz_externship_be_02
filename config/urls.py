import django_eventstream  # type: ignore[import-untyped]
from django.conf import settings
from django.conf.urls.static import static
from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.notifications.views import EventStreamView

urlpatterns: list[URLPattern | URLResolver] = [
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/admin/", include("apps.users.urls.admin_urls")),
    path("api/v1/admin/recruitments", include("apps.recruitments.urls.admin_recruitments_urls")),
    path("api/v1/admin/applications", include("apps.applications.urls.admin_applications_urls")),
    path("api/v1/admin/lectures", include("apps.lectures.urls.admin_urls")),
    path("api/v1/admin/studies", include("apps.studies.urls.admin_urls")),
    path("api/v1/notifications", include("apps.notifications.urls")),
    path("api/v1/lectures", include("apps.lectures.urls.urls", namespace="lectures")),
    path("api/v1/recruitments", include("apps.recruitments.urls")),
    path("api/v1/schedules", include("apps.study_group_schedules.urls")),
    path("api/v1/study-groups", include("apps.studies.urls")),
    path("api/v1/lectures", include("apps.lectures.urls")),
    path("api/v1/study-notes", include("apps.study_notes.urls.study_note_urls")),
    path("api/v1/applications", include("apps.applications.urls")),
    path("api/v1/chat", include("apps.chat.urls")),
    path("events/me", EventStreamView.as_view(), name="events-me"),
    path("events/", include("django_eventstream.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if "debug_toolbar" in settings.INSTALLED_APPS:
        urlpatterns += [path("__debug__", include("debug_toolbar.urls"))]
    if "drf_spectacular" in settings.INSTALLED_APPS:
        urlpatterns += [
            path("api/schema", SpectacularAPIView.as_view(), name="schema"),
            path("api/schema/swagger-ui", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
            path("api/schema/redoc", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
        ]
