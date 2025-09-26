from django.urls import include, path

from apps.applications.views.applications_views import ApplicationAPIView
from apps.recruitments.views.attachments_views import RecruitmentFileView
from apps.recruitments.views.bookmark_views import (
    BookmarkToggleView,
    MyBookmarkedRecruitmentListView,
)
from apps.recruitments.views.images_views import RecruitmentImageView
from apps.recruitments.views.recruitment_detail_views import RecruitmentDetailView
from apps.recruitments.views.recruitment_views import MyRecruitmentView, RecruitmentView

urlpatterns = [
    path("", RecruitmentView.as_view(), name="recruitment-list"),
    path("/me", MyRecruitmentView.as_view(), name="recruitment-mylist"),
    path("/attachments", RecruitmentFileView.as_view(), name="recruitment-attachments-upload"),
    path("/images", RecruitmentImageView.as_view(), name="recruitment-images-upload"),
    path("/<uuid:recruitment_uuid>/applications", ApplicationAPIView.as_view(), name="recruitment-applications"),
    # 북마크 기능 URL
    path("/bookmarks/me", MyBookmarkedRecruitmentListView.as_view(), name="my-bookmark-list"),
    path("/<int:recruitment_id>/bookmarks/", BookmarkToggleView.as_view(), name="recruitment-bookmark"),
    # 상세 조회 URL은 다른 UUID를 사용하는 URL보다 뒤에 위치해야 의도치 않은 매칭을 피할 수 있습니다.
    path("/<uuid:recruitment_uuid>", RecruitmentDetailView.as_view(), name="recruitment-detail"),
]
