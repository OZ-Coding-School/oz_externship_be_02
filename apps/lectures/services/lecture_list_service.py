import json
import logging
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from apps.lectures.models.categories import Category
from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.serializers.crawled_lecture import LectureSerializer

logger = logging.getLogger(__name__)


def get_lectures() -> List[Dict[str, Any]]:
    lectures: Optional[List[Dict[str, Any]]] = None

    cached_lectures = cache.get("lectures:list")
    if cached_lectures:
        try:
            lectures = json.loads(cached_lectures)
        except json.JSONDecodeError:
            logger.warning("\nLectureLog: Redis cached data invalid, fallback to DB")

    # 2. 캐시 없거나 JSON 파싱 실패 시 DB에서 조회
    if lectures is None:
        queryset = Lecture.objects.all()
        serializer = LectureSerializer(queryset, many=True)
        lectures = list(serializer.data)

        # 캐시에 저장
        try:
            cache.set("lectures:list", json.dumps(serializer.data))
        except Exception as e:
            logger.warning("\nLectureLog: Failed to set lectures in cache, skipping: %s", str(e))

    return lectures
