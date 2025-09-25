from django.contrib import admin

from apps.studies.models import StudyReview


@admin.register(StudyReview)
class StudyReviewAdmin(admin.ModelAdmin[StudyReview]):
    # 목록 화면
    list_display = (
        "id",  # 리뷰 PK
        "study_group",  # 스터디 그룹명
        "author",  # 작성자
        "star_rating",  # 별점
        "created_at",  # 생성일시
        "updated_at",  # 수정일시
    )
    search_fields = (
        "author__nickname",  # 작성자 닉네임 검색
        "author__email",  # 작성자 이메일 검색
        "study_group__name",  # 스터디 그룹명 검색
    )
    list_filter = (
        "star_rating",  # 별점으로 필터
        "created_at",  # 생성일 기준 필터
        "updated_at",  # 수정일 기준 필터
    )
    ordering = ("-created_at",)  # 최신순 정렬 (요구사항 반영)

    # 상세 화면
    fields = (
        "id",  # PK
        "study_group",  # 스터디 그룹
        "author",  # 작성자
        "star_rating",  # 별점
        "content",  # 리뷰 내용
        "created_at",  # 생성일시
        "updated_at",  # 수정일시
    )
    readonly_fields = (
        "id",  # PK는 수정 불가
        "created_at",  # 생성일시 수정 불가
        "updated_at",  # 수정일시 수정 불가
    )
