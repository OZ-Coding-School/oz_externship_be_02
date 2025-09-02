from datetime import datetime, timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models.base import UUIDBaseModel
from apps.recruitments.models.tags import Tag
from apps.studies.models import StudyGroup
from apps.users.models.user import User


def get_default_close_at() -> datetime:
    return timezone.now() + timedelta(days=14)


# 스터디 구인 공고 정보
class Recruitment(UUIDBaseModel):
    # StudyGroup.recruitments
    study_group_id = models.ForeignKey(
        StudyGroup, on_delete=models.CASCADE, related_name="recruitments", help_text="스터디 그룹 ID"
    )

    # User.authored_recruitments
    author_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="authored_recruitments", help_text="공고 작성자 ID"
    )

    title = models.CharField(max_length=50, help_text="공고 제목")
    content = models.TextField(help_text="공고 내용")
    estimated_fee = models.IntegerField(help_text="예상 강의 결제 비용")
    expected_headcount = models.SmallIntegerField(
        help_text="예상 모집 인원", validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    views_count = models.IntegerField(default=0, help_text="조회수")
    close_at = models.DateTimeField(default=get_default_close_at, help_text="공고 마감일")
    is_closed = models.BooleanField(default=False, help_text="공고 마감 상태")

    # Recruitment.tags.all()
    # Recruitment.tags.add( , )
    # 내부적으로 RecruitmentTag 자동생성  # 근데 through 빼야됨
    tags = models.ManyToManyField(Tag, through="recruitments.RecruitmentTag", related_name="recruitments")

    # Recruitment.bookmarks.all()
    # User.bookmarked_recruitments
    bookmarks = models.ManyToManyField(
        User, through="recruitments.RecruitmentBookmark", related_name="bookmarked_recruitments"
    )

    class Meta:
        db_table = "recruitments"
        constraints = [
            models.CheckConstraint(
                check=Q(expected_headcount__gte=1) & Q(expected_headcount__lte=10),
                name="recruitment_expected_headcount_range_1_10",
            )
        ]

    def __str__(self) -> str:
        return self.title
