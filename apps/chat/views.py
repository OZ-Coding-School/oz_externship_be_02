from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from django.shortcuts import get_object_or_404

class ChatRoomListView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    # 채팅방 목록 조회
    def list(self, request):
        user = request.user
        queryset = ChatMessage.objects.filter(study_group__members=user).order_by('study_group', '-created_at').distinct('study_group')
        serializer = ChatMessageSerializer(queryset, many=True)
        return Response(serializer.data)
