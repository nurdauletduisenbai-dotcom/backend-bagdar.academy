from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import CommentViewSet, LessonViewSet, MaterialViewSet, SectionViewSet

router = SimpleRouter()
router.register(r'sections', SectionViewSet, basename='sections')
router.register(r'lessons', LessonViewSet, basename='lessons')
router.register(r'materials', MaterialViewSet, basename='materials')
router.register(r'comments', CommentViewSet, basename='comments')

urlpatterns = [path('', include(router.urls))]
