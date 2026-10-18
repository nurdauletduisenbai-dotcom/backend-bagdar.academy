from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import CourseViewSet

router = SimpleRouter()
router.register(r'', CourseViewSet, basename='courses')

urlpatterns = [
    path('', include(router.urls)),
]
