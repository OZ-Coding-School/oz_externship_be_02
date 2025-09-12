from apps.recruitments.managers.managers_list import RecruitmentListQuerySet
from apps.recruitments.models.recruitments import Recruitment


def active_get_query() -> RecruitmentListQuerySet:
    # 마감된 공고는 필터하고 최신순을 기본 정렬로 함
    # 시리얼라이저 정보 최적화하여 채워넣기
    queryset = Recruitment.object_list.filter_is_closed().order_last().optimized_queryset()
    return queryset


def filter_tag(queryset: RecruitmentListQuerySet, tag: str) -> RecruitmentListQuerySet:
    filtered_queryset = queryset.filter(tags__name=tag)
    return filtered_queryset


def filter_category(queryset: RecruitmentListQuerySet, category: str) -> RecruitmentListQuerySet:
    filtered_queryset = queryset.filter(study_group__lectures__categories__name=category).distinct()
    return filtered_queryset
