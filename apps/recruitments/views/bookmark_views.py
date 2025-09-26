from typing import Any, cast

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.paginators import DefaultCursorPagination
from apps.recruitments.serializers.bookmark_serializers import (
    MyBookmarkedRecruitmentListSerializer,
)
from apps.recruitments.services.bookmark_services import BookmarkService
from apps.users.models import User


class BookmarkToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, recruitment_id: int) -> Response:
        service = BookmarkService()
        try:
            _, created = service.add(user=cast(User, request.user), recruitment_id=recruitment_id)
            if created:
                return Response({"detail": "북마크가 추가되었습니다."}, status=status.HTTP_201_CREATED)
            return Response({"detail": "이미 북마크되어 있습니다."}, status=status.HTTP_200_OK)
        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request: Request, recruitment_id: int) -> Response:
        service = BookmarkService()
        try:
            service.remove(user=cast(User, request.user), recruitment_id=recruitment_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


class MyBookmarkedRecruitmentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        service = BookmarkService()
        queryset = service.get_bookmarked_list(user=cast(User, request.user))

        paginator = DefaultCursorPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)

        serializer = MyBookmarkedRecruitmentListSerializer(paginated_queryset, many=True)
        paginated_data = cast(list[dict[str, Any]], serializer.data)
        return paginator.get_paginated_response(paginated_data)
