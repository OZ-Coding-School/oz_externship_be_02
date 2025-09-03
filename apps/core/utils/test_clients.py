from rest_framework.test import APITestCase
from django.test import override_settings
from django_redis import get_redis_connection


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://localhost:6379/15",  # test redis
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient"
            },
        }
    }
)
class RedisTestClient(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.redis_client = get_redis_connection("default")

    def tearDown(self):
        self.redis_client.flushdb()  # 현재 DB만 초기화
        super().tearDown()
