from django.urls import URLPattern, URLResolver, include, path

from apps.lectures.urls.admin_urls import urlpatterns as admin_urls
from apps.lectures.urls.bookmarks_urls import urlpatterns as bookmark_urls

urlpatterns: list[URLPattern | URLResolver] = [
    *bookmark_urls,
    path("/admin/lectures", include((admin_urls, "admin-lectures"), namespace="admin-lectures")),
]
