from apps.recruitments.managers.managers_list import RecruitmentListQuerySet
from apps.recruitments.models.recruitments import Recruitment
from apps.users.models.user import User


def active_get_query() -> RecruitmentListQuerySet:
    # 마감된 공고는 필터하고 최신순을 기본 정렬로 함
    # 시리얼라이저 정보 최적화하여 채워넣기
    queryset = Recruitment.object_list.filter_is_closed().order_last().optimized_queryset()
    return queryset


def filter_tag(queryset: RecruitmentListQuerySet, tag: str) -> RecruitmentListQuerySet:
    filtered_queryset = queryset.filter(tags__name=tag)
    return filtered_queryset


def active_get_my_query(user: User) -> RecruitmentListQuerySet:
    queryset = Recruitment.object_list.order_last().optimized_queryset().filter(author=user)
    return queryset


def filter_is_closed(queryset: RecruitmentListQuerySet, is_closed: bool) -> RecruitmentListQuerySet:
    filtered_queryset = queryset.filter(is_closed=is_closed)
    return filtered_queryset
