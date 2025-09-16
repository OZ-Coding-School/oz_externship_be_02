from django.db.models import QuerySet
from django_filters import rest_framework as filters

from apps.users.models import User

# 필터링 옵션
PERMISSION_CHOICES = (
    ("admin", "관리자"),
    ("staff", "스태프"),
    ("general", "일반회원"),
)
STATUS_CHOICES = (
    ("active", "활성화"),
    ("inactive", "비활성화"),
    ("withdrawn", "탈퇴진행중"),
)


class UserFilter(filters.FilterSet):
    # 'permission'이라는 이름으로 필터 파라미터를 추가
    permission = filters.ChoiceFilter(choices=PERMISSION_CHOICES, method="filter_by_permission")
    # 'status'라는 이름으로 필터 파라미터를 추가
    status = filters.ChoiceFilter(choices=STATUS_CHOICES, method="filter_by_status")

    class Meta:
        model = User
        fields = ["permission", "status"]

    def filter_by_permission(self, queryset: QuerySet[User], name: str, value: str) -> QuerySet[User]:
        # 파라미터 값에 따라 is_superuser와 is_staff 값을 조합해서 필터링
        if value == "admin":
            return queryset.filter(is_superuser=True)
        if value == "staff":
            return queryset.filter(is_staff=True, is_superuser=False)
        if value == "general":
            return queryset.filter(is_staff=False, is_superuser=False)
        return queryset

    def filter_by_status(self, queryset: QuerySet[User], name: str, value: str) -> QuerySet[User]:
        # status 파리미터 값에 따라 필터링 로직 분기
        if value == "withdrawn":
            # withdrawals 테이블에 존재하는 유저만 필터링
            return queryset.filter(withdrawals__isnull=False)

        # active 또는 inactive인 경우, 탈퇴 신청을 하지 않은 유저 중에서 필터링
        is_active = value == "active"
        return queryset.filter(withdrawals__isnull=True, is_active=is_active)
