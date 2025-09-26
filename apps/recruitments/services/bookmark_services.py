from django.db.models.query import QuerySet
from rest_framework.exceptions import NotFound

from apps.recruitments.models import Recruitment, RecruitmentBookmark
from apps.users.models import User


class BookmarkService:
    def _get_recruitment(self, recruitment_id: int) -> Recruitment:
        try:
            return Recruitment.objects.get(id=recruitment_id)
        except Recruitment.DoesNotExist:
            raise NotFound("해당 스터디 구인 공고는 존재하지 않습니다.")

    def add(self, user: User, recruitment_id: int) -> tuple["RecruitmentBookmark", bool]:
        recruitment = self._get_recruitment(recruitment_id)
        bookmark, created = RecruitmentBookmark.objects.add_bookmark(user=user, recruitment=recruitment)
        return bookmark, created

    def remove(self, user: User, recruitment_id: int) -> None:
        recruitment = self._get_recruitment(recruitment_id)
        deleted_count, _ = RecruitmentBookmark.objects.remove_bookmark(user=user, recruitment=recruitment)
        if deleted_count == 0:
            raise NotFound("북마크 내역이 존재하지 않습니다.")

    def get_bookmarked_list(self, user: User) -> QuerySet[Recruitment]:
        return Recruitment.object_list.get_bookmarked_recruitments(user=user)
