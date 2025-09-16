
def preferred_lectures(self, request, lectures):
    # Get Search Contents
    search = request.query_params.get("search")
    search = search.lower()
    # ORM Logic, Preprocessing
    self.save_search_history(search, request)
    # Algorithm
    var1 = self.extract_keywords_from_search_history()
    var2 = self.extract_preferred_categories()
    three_preferred_lectures = self.cbf_algorithm(var1, var2, lectures)

    return three_preferred_lectures


def save_search_history(self, search, request):
    if not request.user.is_authenticated:
        return
    keyword = f"filtered{search}"  # 단순 전처리 예시
    try:
        LectureSearchLog.objects.create(
            user=request.user,
            keyword=keyword
        )
        logger.info("LectureLog: Saved keyword='%s' for user=%s", keyword, request.user.id)
    except Exception as e:
        logger.error("LectureLog: Failed to save search for user=%s, reason=%s", request.user.id, str(e))


def extract_preferred_categories(self):
    user = request.user
    if not user.is_authenticated:
        return []
    preferred_categories = (
        UserPreferCategory.objects
        .filter(user=user)
        .select_related("category")  # category 객체 접근 효율화
        .values_list("category__name", flat=True)
    )

    return list(preferred_categories)


def extract_keywords_from_search_history(self):
    user = request.user
    if not user.is_authenticated:
        return []

    recent_keywords = (
        LectureSearchLog.objects
        .filter(user=user)
        .order_by("-searched_at")[:10]
        .values_list("keyword", flat=True)
    )
    return list(recent_keywords)


def cbf_algorithm(self, search_keywords, preferred_categories, lectures):
    lecture_texts = [
        f"{lecture['title']} {lecture['category']}" for lecture in lectures
    ]

    # 3️⃣ 유저 프로필 텍스트 생성 (검색 키워드 + 선호 카테고리)
    user_profile_text = "".join(search_keywords + preferred_categories)

    # 4️⃣ TF-IDF 벡터화
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(lecture_texts + [user_profile_text])

    # 5️⃣ 코사인 유사도 계산 (마지막 벡터가 유저)
    user_vector = tfidf_matrix[-1]
    lecture_vectors = tfidf_matrix[:-1]
    similarities = cosine_similarity(user_vector, lecture_vectors).flatten()

    # 6️⃣ 유사도 기준 정렬 후 상위 3개 추천
    top_indices = similarities.argsort()[::-1][:3]
    recommended = [lectures[i]["title"] for i in top_indices]

    return recommended
