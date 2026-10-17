from django.urls import path
from .views import VideoPlayView, VideoProgressView

urlpatterns = [
    path('<int:video_id>/play/', VideoPlayView.as_view(), name='video_play'),
    path('<int:video_id>/progress/', VideoProgressView.as_view(), name='video_progress'),
]
