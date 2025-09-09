from apps.recruitments.urls.recruitments_urls import urlpatterns as recruitments_urls
from apps.recruitments.urls.tags_urls import urlpatterns as tags_urls

# app_name = "recruitments"

urlpatterns = recruitments_urls + tags_urls
