from datetime import date, datetime
from typing import Any, Dict, List

from django.utils import timezone

from apps.studies.models import GroupMember, StudyGroup
from apps.study_notes.models import StudyNote, StudyNoteAttachment, StudyNoteImage
from apps.users.models.user import User


# 유저 생성
def create_mock_users(count: int = 10) -> List[User]:
    users = []
    for i in range(count):
        user = User.objects.create_user(
            email=f"user{i+1}@test.com",
            password="testpassword123",
            nickname=f"nick{i+1}",
            name=f"User{i+1}",
            phone_number=f"0101000000{i+1:02d}",
            gender="M" if i % 2 == 0 else "F",
            birthday=date(2000, 1, i + 1),  # 테스트용 날짜, i+1일로 구분
        )
        users.append(user)
    return users


# 스터디 그룹 생성
def create_mock_study_groups() -> List[StudyGroup]:
    group1 = StudyGroup.objects.create(
        name="스터디그룹1",
        introduction="테스트 그룹 1",
        max_headcount=5,
        profile_img_url="https://example.com/group1.png",
        start_at=timezone.make_aware(datetime(2025, 9, 1, 10, 0)),
        end_at=timezone.make_aware(datetime(2025, 9, 1, 10, 0)),
        status="PENDING",
    )
    group2 = StudyGroup.objects.create(
        name="스터디그룹2",
        introduction="테스트 그룹 2",
        max_headcount=10,
        profile_img_url="https://example.com/group2.png",
        start_at=timezone.make_aware(datetime(2025, 9, 1, 10, 0)),
        end_at=timezone.make_aware(datetime(2025, 9, 1, 10, 0)),
        status="PENDING",
    )

    return [group1, group2]


# 그룹 맴버 추가
def add_users_to_groups(users: List[User], groups: List[StudyGroup]) -> None:
    for user in users[0:5]:
        GroupMember.objects.create(user=user, study_group=groups[0])
    for user in users[6:9]:
        GroupMember.objects.create(user=user, study_group=groups[1])


# 스터디 노트 생성
def create_mock_notes(users: List[User], groups: List[StudyGroup]) -> List[StudyNote]:
    notes = []

    note1 = StudyNote.objects.create(
        study_group=groups[0],
        author=users[0],
        title="그룹1 노트1 제목",
        content="그룹1 노트1 내용",
        ai_summary="그룹1 노트1 AI 요약",
    )
    StudyNoteImage.objects.create(study_note=note1, img_url="https://example.com/note1_img.png")
    StudyNoteAttachment.objects.create(
        study_note=note1, file_url="https://example.com/note1_file.pdf", file_name="note1_file.pdf"
    )
    notes.append(note1)

    note2 = StudyNote.objects.create(
        study_group=groups[1],
        author=users[3],
        title="그룹2 노트1 제목",
        content="그룹2 노트1 내용",
        ai_summary="그룹2 노트1 AI 요약",
    )
    StudyNoteImage.objects.create(study_note=note2, img_url="https://example.com/note2_img.png")
    StudyNoteAttachment.objects.create(
        study_note=note2, file_url="https://example.com/note2_file.pdf", file_name="note2_file.pdf"
    )
    notes.append(note2)

    return notes


# 모든 데이터 생성
def create_all_mock_data() -> Dict[str, Any]:
    users = create_mock_users()
    groups = create_mock_study_groups()
    add_users_to_groups(users, groups)
    notes = create_mock_notes(users, groups)
    return {"users": users, "groups": groups, "notes": notes}
