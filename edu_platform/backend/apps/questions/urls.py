from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import QuestionViewSet, TopicViewSet

router = SimpleRouter()
router.register(r'topics', TopicViewSet, basename='topics')
router.register(r'questions', QuestionViewSet, basename='questions')

urlpatterns = [path('', include(router.urls))]
