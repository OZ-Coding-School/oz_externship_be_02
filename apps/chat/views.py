from django.db import models
from rest_framework.views import APIView
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from django.shortcuts import get_object_or_404
from apps.users import serializers
from django.contrib.auth.models import User

class ChatRoomListView(models.Model):

    # 채팅방 목록 조회
    def get(self, request):
        user = request.user
        queryset = User.objects.all()
        serializer = User.objects.all()
        return Response(serializer.data)

        def get_queryset(self):
            # 유저가 속한 그터디 그룹의 메세지만!
            return

