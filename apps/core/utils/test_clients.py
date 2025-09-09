from django.conf import settings
from django.test import override_settings
from django_redis import get_redis_connection  # type: ignore
from rest_framework.test import APITestCase


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{settings.REDIS_HOST}:6379/15",  # test redis
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }
)
class RedisTestClient(APITestCase):
    redis_client = get_redis_connection("default")

    def tearDown(self) -> None:
        self.redis_client.flushdb()  # 현재 DB만 초기화
        super().tearDown()
