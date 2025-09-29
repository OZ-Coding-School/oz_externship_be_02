from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from apps.lectures.models.crawled_lectures import Lecture
from apps.lectures.models.lecture_search_logs import LectureSearchLog
from apps.lectures.models.user_prefer_categories import UserPreferCategory
from apps.lectures.serializers.crawled_lecture import LectureSerializer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RecommendLectureService:
    page_size = 3
    serializer_class = LectureSerializer
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        # 전체 강의 조회 및 직렬화
        lectures = Lecture.objects.all()
        serializer = self.serializer_class(lectures, many=True)
        lectures_data = serializer.data

        # 유저 기반 추천
        if request.user.is_authenticated:
            recommended = self.preferred_lectures(request, lectures_data)
        else:
            recommended = lectures_data[:self.page_size]

        return Response({"results": recommended})

    # 추천 강의 추출
    def preferred_lectures(self, request, lectures):
        serializer = self.serializer_class(lectures, many=True)
        lectures_data = serializer.data  # dict list

        search_keywords = self.extract_keywords_from_search_history(request.user)
        preferred_categories = self.extract_preferred_categories(request.user)

        return self.cbf_algorithm(search_keywords, preferred_categories, lectures_data)
    # 최근 검색 기록
    def extract_keywords_from_search_history(self, user):
        recent_keywords = (
            LectureSearchLog.objects
            .filter(user=user)
            .order_by("-created_at")[:10]
            .values_list("keyword", flat=True)
        )
        return list(recent_keywords)

    # 선호 카테고리
    def extract_preferred_categories(self, user):
        preferred_categories = (
            UserPreferCategory.objects
            .filter(user=user)
            .select_related("category")
            .values_list("category__name", flat=True)
        )
        return list(preferred_categories)

    # CBF 알고리즘
    def cbf_algorithm(self, search_keywords, preferred_categories, lectures):
        if not lectures:
            return []

        lecture_texts = [
            f"{lecture['title']} {lecture.get('categories', '')}" for lecture in lectures
        ]
        user_profile_text = " ".join(search_keywords + preferred_categories)

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(lecture_texts + [user_profile_text])

        user_vector = tfidf_matrix[-1]
        lecture_vectors = tfidf_matrix[:-1]
        similarities = cosine_similarity(user_vector, lecture_vectors).flatten()

        top_indices = similarities.argsort()[::-1][:self.page_size]
        recommended = [lectures[i] for i in top_indices]

        return recommended
