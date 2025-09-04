from datetime import datetime

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class RecruitmentDetailView(APIView):
    permission_classes = [AllowAny]  # 누구나 접근 가능(인증 불필요)

    def get(self, request, recruitmentId):

        mock_data = {
            "id": recruitmentId,
            "uuid": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "author": {"id": 1, "nickname": "해파리볶음밥"},
            "title": "Mock API: Mock 깜빡하고 뒤늦게 만든 최재현, 그는 바보인가!?",
            "content": "이것은 실제 데이터가 아닌 Mock 데이터입니다.",
            "attachments": [
                {"file_name": "study_plan_mock.pdf", "file_url": "http://example.com/mock.pdf"}
            ],  # 첨부파일 이름/이미지url
            "expected_headcount": 4,  # 예상 모집인원
            "estimated_fee": 20000,  # 추정 수수료
            "lectures": [
                {
                    "thumbnail_image_url": "http://example.com/lecture_thumbnail.jpg",
                    "name": "개바렁렵다",
                    "instructor": "최재현",
                    "url": "http://example.com/lecture/1",
                }
            ],
            "tags": [{"name": "#Django"}],
            "deadline": datetime(2025, 9, 30, 15, 00, 00).isoformat(),  # 마감기한
            "created_at": datetime(2025, 9, 3, 5, 24, 0).isoformat(),  # 공고 등록일시
            "view_count": 123,
            "bookmark_count": 5,
        }

        # 가데이터 통과 시 200 응답
        return Response(mock_data, status=status.HTTP_200_OK)

    def patch(self, request, recruitmentId):
        # 아직 구현 전. 다른 브랜치에서 구현할 것
        pass

    def delete(self, request, recruitmentId):
        # 아직 구현 전. 다른 브랜치에서 구현할 것
        pass
