from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import VideoPlayView, VideoProgressView, VideoViewSet

router = SimpleRouter()
router.register(r'', VideoViewSet, basename='videos')

urlpatterns = [
    path('<int:video_id>/play/', VideoPlayView.as_view(), name='video_play'),
    path('<int:video_id>/progress/', VideoProgressView.as_view(), name='video_progress'),
    path('', include(router.urls)),
]
