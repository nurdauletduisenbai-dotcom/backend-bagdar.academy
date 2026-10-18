from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import AuditLogViewSet

router = SimpleRouter()
router.register(r'logs', AuditLogViewSet, basename='audit-logs')

urlpatterns = [path('', include(router.urls))]
