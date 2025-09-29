from apps.studies.urls.review_urls import urlpatterns as review_urls
from apps.studies.urls.study_group import urlpatterns as study_group_urls
from apps.studies.urls.admin_urls import urlpatterns as admin_urls

urlpatterns = review_urls + study_group_urls + admin_urls
