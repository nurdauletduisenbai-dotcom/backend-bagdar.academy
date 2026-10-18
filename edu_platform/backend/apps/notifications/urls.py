from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import AnnouncementViewSet, NotificationPreferenceView, NotificationViewSet

router = SimpleRouter()
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'announcements', AnnouncementViewSet, basename='announcements')

urlpatterns = [
    path('notifications/preferences/', NotificationPreferenceView.as_view(), name='notification_preferences'),
    path('', include(router.urls)),
]
