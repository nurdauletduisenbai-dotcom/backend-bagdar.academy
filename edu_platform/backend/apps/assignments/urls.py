from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import AssignmentViewSet, SubmissionViewSet

router = SimpleRouter()
router.register(r'assignments', AssignmentViewSet, basename='assignments')
router.register(r'submissions', SubmissionViewSet, basename='submissions')

urlpatterns = [path('', include(router.urls))]
