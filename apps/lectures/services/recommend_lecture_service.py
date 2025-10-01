from typing import Any, Dict, List

from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
from sklearn.metrics.pairwise import cosine_similarity  # type: ignore

from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_search_logs import LectureSearchLog
from apps.lectures.models.user_prefer_categories import UserPreferCategory
from apps.lectures.serializers.crawled_lecture import LectureSerializer
from apps.users.models.user import User


class RecommendLectureService:
    page_size: int = 3
    serializer_class = LectureSerializer
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        # 전체 강의 조회 및 직렬화
        queryset = Lecture.objects.all()
        serializer = self.serializer_class(queryset, many=True)
        lectures_data: List[Dict[str, Any]] = list(serializer.data)

        # 유저 기반 추천
        user = request.user
        if user.is_authenticated and not isinstance(user, AnonymousUser):
            recommended: List[Dict[str, Any]] = self.preferred_lectures(user, lectures_data)
        else:
            recommended = lectures_data[: self.page_size]

        return Response({"results": recommended})

    # 추천 강의 추출
    def preferred_lectures(self, user: User, lectures_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # 로그인 여부 체크
        if not user.is_authenticated or isinstance(user, AnonymousUser):
            return lectures_data[: self.page_size]

        search_keywords: List[str] = self.extract_keywords_from_search_history(user)
        preferred_categories: List[str] = self.extract_preferred_categories(user)
        return self.cbf_algorithm(search_keywords, preferred_categories, lectures_data)

    # 최근 검색 기록
    def extract_keywords_from_search_history(self, user: User) -> List[str]:
        recent_keywords = (
            LectureSearchLog.objects.filter(user=user).order_by("-created_at")[:10].values_list("keyword", flat=True)
        )
        return list(recent_keywords)

    # 선호 카테고리
    def extract_preferred_categories(self, user: User) -> List[str]:
        preferred_categories = (
            UserPreferCategory.objects.filter(user=user)
            .select_related("category")
            .values_list("category__name", flat=True)
        )
        return list(preferred_categories)

    # CBF 알고리즘
    def cbf_algorithm(
        self,
        search_keywords: List[str],
        preferred_categories: List[str],
        lectures: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not lectures:
            return []

        # 강의 제목 + 카테고리 텍스트 생성
        lecture_texts: List[str] = [
            f"{lecture['title']} {' '.join(lecture.get('categories', [])) if isinstance(lecture.get('categories'), list) else lecture.get('categories', '')}"
            for lecture in lectures
        ]
        user_profile_text: str = " ".join(search_keywords + preferred_categories)

        # TF-IDF 벡터화
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(lecture_texts + [user_profile_text])

        user_vector = tfidf_matrix[-1]
        lecture_vectors = tfidf_matrix[:-1]
        similarities = cosine_similarity(user_vector, lecture_vectors).flatten()

        # 상위 page_size 강의 추천
        top_indices = similarities.argsort()[::-1][: self.page_size]
        recommended: List[Dict[str, Any]] = [lectures[i] for i in top_indices]

        return recommended
