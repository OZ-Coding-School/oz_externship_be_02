from django.urls import path

from .views import ChatMessageListView, ChatRoomListView

urlpatterns = [
    path("/rooms", ChatRoomListView.as_view(), name="chatroom-list"),
    path("/<uuid:study_group_uuid>/messages", ChatMessageListView.as_view(), name="message-list"),
]
