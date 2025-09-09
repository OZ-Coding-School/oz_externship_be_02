from apps.recruitments.managers.managers_list import RecruitmentListQuerySet
from apps.recruitments.models.recruitments import Recruitment


def active_get_query() -> RecruitmentListQuerySet[Recruitment]:
    # 마감된 공고는 필터하고 최신순을 기본 정렬로 함
    # 시리얼라이저 정보 최적화하여 채워넣기
    queryset = Recruitment.object_list.filter_is_closed().order_last().optimized_queryset()
    return queryset
