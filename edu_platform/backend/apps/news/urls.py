from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import ContactRequestView, PlatformStatsView, PostViewSet

router = SimpleRouter()
router.register(r'posts', PostViewSet, basename='news-posts')

urlpatterns = [
    path('stats/', PlatformStatsView.as_view(), name='news-stats'),
    path('contact/', ContactRequestView.as_view(), name='news-contact'),
    path('', include(router.urls)),
]
