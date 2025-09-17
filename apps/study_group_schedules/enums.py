from enum import Enum


class ScheduleOrdering(str, Enum):
    """스케줄 정렬 옵션"""

    DATE_ASC = "session_date"  # 날짜순 (오래된 것부터)
    DATE_DESC = "-session_date"  # 날짜 역순 (최신 것부터)
    TIME_ASC = "start_time"  # 시간순
    TIME_DESC = "-start_time"  # 시간 역순
    CREATED_DESC = "-created_at"  # 생성일 역순

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """Django ChoiceField용 choices 반환"""
        return [
            (cls.DATE_ASC.value, "날짜순"),
            (cls.DATE_DESC.value, "날짜 역순"),
        ]

    @classmethod
    def default(cls) -> str:
        """기본 정렬 옵션"""
        return cls.DATE_DESC.value
