from django.shortcuts import get_object_or_404
from apps.recruitments.models import Recruitment

# 상세정보 조회용 서비스함수.
def get_recruitment_details(recruitment_id: int):
    recruitment = get_object_or_404(
        Recruitment.objects.prefetch_related('tags', 'attachments'),
        id=recruitment_id
    )

    # 조회수 증가같은 비즈니스용 로직
    recruitment.views_count += 1
    recruitment.save(update_fields=['views_count'])

    return recruitment