from django.urls import path

from .views import ChatMessageListView, ChatRoomListView

urlpatterns = [
    path("/rooms/", ChatRoomListView.as_view(), name="chatroom-list"),
    path("/rooms/<str:study_group_uuid>/messages/", ChatMessageListView.as_view(), name="chat-message-by-room"),
]
