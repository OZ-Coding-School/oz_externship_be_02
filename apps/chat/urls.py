from django.urls import path

from .views import ChatRoomListView, ChatMessageListView

urlpatterns = [
    path("/rooms/", ChatRoomListView.as_view(), name="chatroom-list"),
    path("/rooms/<str:study_group_uuid>/messages/", ChatMessageListView.as_view(), name='chat-message-by-room'),
]
