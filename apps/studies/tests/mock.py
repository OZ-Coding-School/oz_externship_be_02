from datetime import date

from apps.users.models.user import User


def create_mock_users(count: int = 10) -> list[User]:
    """
    가상 유저 데이터 생성
    :param count: 생성할 유저 데이터 개수
    :return: 생성된 유저 데이터
    """
    users = []
    for i in range(count):
        user = User.objects.create_user(
            email=f"user{i + 1}@test.com",
            password="testpassword123",
            nickname=f"nick{i + 1}",
            name=f"User{i + 1}",
            phone_number=f"0101000000{i + 1:02d}",
            gender="M" if i % 2 == 0 else "F",
            birthday=date(2000, 1, i + 1),  # 테스트용 날짜, i+1일로 구분
        )
        users.append(user)
    return users
