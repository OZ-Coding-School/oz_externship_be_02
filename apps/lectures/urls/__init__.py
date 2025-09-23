from django.urls import URLPattern, URLResolver

from apps.lectures.urls.bookmarks_urls import urlpatterns as bookmark_urls

urlpatterns: list[URLPattern | URLResolver] = [*bookmark_urls]
