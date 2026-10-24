from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import PlatformStatsView, PostViewSet

router = SimpleRouter()
router.register(r'posts', PostViewSet, basename='news-posts')

urlpatterns = [
    path('stats/', PlatformStatsView.as_view(), name='news-stats'),
    path('', include(router.urls)),
]
