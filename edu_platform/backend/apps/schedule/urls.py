from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import AttendanceViewSet, GroupViewSet, SessionViewSet

router = SimpleRouter()
router.register(r'groups', GroupViewSet, basename='groups')
router.register(r'sessions', SessionViewSet, basename='sessions')
router.register(r'attendance', AttendanceViewSet, basename='attendance')

urlpatterns = [path('', include(router.urls))]
