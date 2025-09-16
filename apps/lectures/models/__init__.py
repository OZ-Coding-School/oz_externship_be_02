from .categories import Category
from .crawled_lecture_reviews import LectureReview
from .crawled_lectures import Lecture
from .lecture_bookmarks import LectureBookmark
from .lecture_categories import LectureCategory
from .lecture_search_logs import LectureSearchLog
from .user_prefer_categories import UserPreferCategory

__all__ = [
    "Lecture",
    "LectureBookmark",
    "LectureCategory",
    "LectureReview",
    "LectureSearchLog",
    "Category",
    "UserPreferCategory",
]
