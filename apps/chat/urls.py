from rest_framework.routers import DefaultRouter
from .views import ChatRoomListView
from django.urls import path

router = DefaultRouter()
router.register('messages', ChatRoomListView, basename='chatroom')

urlpatterns = [
    path("", ChatRoomListView.as_view(), name='chatroomlist'),
]