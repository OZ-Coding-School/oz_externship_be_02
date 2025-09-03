from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

# 아직 Service나 Serializer는 사용하지 않습니다.

class RecruitmentDetailView(APIView):
    #구인 공고 상세 조회 (GET) Mock API
    #Endpoint: /api/v1/recruitments/{recruitmentId}
    permission_classes = [IsAuthenticated] # 인증 검사는 그대로 유지

    # Mock API 구현:REQ-RECM-006
    def get(self, request, recruitmentId):
        # 1. API 명세서에 정의된 '성공 응답'과 똑같은 모양의 가짜 데이터를 만듭니다.
        mock_data = {
            "id": recruitmentId,
            "uuid": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "author": {
                "id": 1,
                "nickname": "해파리볶음밥"
            },
            "title": "Mock API: Mock 깜빡하고 뒤늦게 만든 최재현, 그는 바보인가!?",
            "content": "이것은 실제 데이터가 아닌 Mock 데이터입니다. 다급하게 지피티를 통해 만들었으므로, 내용부실이 있을 수 있습니다.",
            "attachments": [
                {
                    "file_name": "study_plan_mock.pdf",
                    "file_url": "http://example.com/mock.pdf"
                }
            ],
            "recruit_count": 4,
            "cost": 316000,
            "tags": [
                {"name": "#Django"},
                {"name": "#MockAPI"}
            ],
            "deadline": "2025-09-05/DeadlineTime:p.m 4:00",
            "created_at": "2025-09-03/CreatedTime:p.m 4:30",
            "view_count": 123,
            "bookmark_count": 5
        }
        
        # 가짜데이터가 통과되면 200 OK 응답
        return Response(mock_data, status=status.HTTP_200_OK)

    def patch(self, request, recruitmentId):
        # 아직 구현 전. 다른 브랜치에서 구현할 것
        pass

    def delete(self, request, recruitmentId):
        # 아직 구현 전. 다른 브랜치에서 구현할 것
        pass