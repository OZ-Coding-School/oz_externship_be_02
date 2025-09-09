from apps.recruitments.urls.recruitments_urls import urlpatterns as recruitments_urls
from apps.recruitments.urls.tags_urls import urlpatterns as tags_urls
from apps.recruitments.urls.urls_list import urlpatterns as urls_list

urlpatterns = [
    *recruitments_urls,
    *tags_urls,
    *urls_list,
]
