from apps.users.urls.auth_urls import urlpatterns as auth_urls
from apps.users.urls.users_urls import urlpatterns as users_urls

urlpatterns = auth_urls + users_urls
