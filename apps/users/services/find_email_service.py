from rest_framework.exceptions import NotFound

from apps.users.models.user import User


class FindEmailService:
    @staticmethod
    def find_email(name: str, phone_number: str) -> str:
        """
        이름과 (인증된) 휴대폰 번호로 사용자 이메일 조회
        """
        try:
            user = User.objects.get(name=name, phone_number=phone_number)
        except User.DoesNotExist:
            raise NotFound("사용자를 찾을 수 없습니다.")  # 404 처리용 예외

        return user.email
