import logging
from datetime import date

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.users.models.withdrawals import Withdrawals

User = get_user_model()
logger = logging.getLogger(__name__)  # 테스크의 파일 로거 생성


@shared_task
def delete_expired_withdrawals_users() -> None:
    """
    탈퇴 유예 기간(due_date)이 지난 사용자 계정을 영구 삭제
    """
    # 오늘 날짜
    today = date.today()

    # due_date가 오늘이거나 오늘보다 이전인 객체 핉터링
    expired_withdrawals = Withdrawals.objects.filter(due_date__lte=today, user__isnull=False)

    if expired_withdrawals.exists():
        with transaction.atomic():
            for withdrawal in expired_withdrawals:
                # 사용자 객체 삭제 기록은 유지
                try:
                    user_to_delete = withdrawal.user
                    if user_to_delete:
                        user_email = user_to_delete.email
                        user_to_delete.delete()
                        logger.info(f"사용자 계정 삭제: {user_email}")  # info 레벨로 성공 로그
                except User.DoesNotExist:
                    logger.warning(f"이미 삭제되었거나 존재하지 않는 사용자입니다. (탈퇴 요청 ID: {withdrawal.id})")
                except Exception as e:
                    logger.error(
                        f"사용자 계정 삭제 중 오류 발생 (탈퇴 요청 ID: {withdrawal.id}, 오류: {e})", exc_info=True
                    )
    else:
        logger.info("만료된 탈퇴 요청이 없습니다")  # 정상적인 상황 기록
