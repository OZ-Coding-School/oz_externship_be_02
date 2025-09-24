from django.urls import path

from .views import ChatRoomListView

urlpatterns = [
    path("/rooms", ChatRoomListView.as_view(), name="chatroom-list"),
]
