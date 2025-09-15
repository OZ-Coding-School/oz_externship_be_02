from rest_framework.routers import DefaultRouter

from .models import ChatMessage
from .views import ChatRoomListView

router = DefaultRouter()
router.register('messages', ChatRoomListView)