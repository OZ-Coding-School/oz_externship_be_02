from rest_framework.routers import DefaultRouter
from .views import ChatRoomListView

router = DefaultRouter()
router.register('messages', ChatRoomListView, basename='chatroom')

urlpatterns = router.urls