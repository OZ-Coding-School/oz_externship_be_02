from django.urls import URLPattern, URLResolver, include, path

from apps.lectures.urls.bookmarks_urls import urlpatterns as bookmark_urls
from apps.lectures.urls.urls import urlpatterns as lecture_urls

urlpatterns: list[URLPattern | URLResolver] = [*bookmark_urls, *lecture_urls]
