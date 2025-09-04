from datetime import datetime

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class RecruitmentDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, recruitment_id: int) -> Response:

        mock_data = {
            "id": recruitment_id,
            "uuid": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "author": {"id": 1, "nickname": "해파리볶음밥"},
            "title": "Mock API: Mock 깜빡하고 뒤늦게 만든 최재현, 그는 바보인가!?",
            "content": "이것은 실제 데이터가 아닌 Mock 데이터입니다.",
            "attachments": [{"file_name": "study_plan_mock.pdf", "file_url": "http://example.com/mock.pdf"}],
            "expected_headcount": 4,
            "estimated_fee": 20000,
            "lectures": [
                {
                    "thumbnail_image_url": "http://example.com/lecture_thumbnail.jpg",
                    "name": "개바렁렵다",
                    "instructor": "최재현",
                    "url": "http://example.com/lecture/1",
                }
            ],
            "tags": [{"name": "#Django"}],
            "deadline": datetime(2025, 9, 30, 15, 00, 00).isoformat(),
            "created_at": datetime(2025, 9, 3, 5, 24, 0).isoformat(),
            "view_count": 123,
            "bookmark_count": 5,
        }

        return Response(mock_data, status=status.HTTP_200_OK)

    # 다음 브랜치에서 구현 예정
    def patch(self, request: Request, recruitmentId: int) -> Response:
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    # 501은 구현되지 않았음을 알리는 코드
    def delete(self, request: Request, recruitmentId: int) -> Response:
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
