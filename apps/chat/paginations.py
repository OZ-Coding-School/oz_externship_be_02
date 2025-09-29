from rest_framework.pagination import CursorPagination


class ChatMessageCursorPagination(CursorPagination):
    # 채팅 메시지용 커서 페이지 네이션
    page_size = 100
    max_page_size = 300
    ordering = "-created_at"
    cursor_query_param = "cursor"
    page_size_query_param = "page_size"
