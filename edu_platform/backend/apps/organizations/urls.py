from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    CurrentOrganizationView,
    InviteCreateView,
    InviteListView,
    InviteRevokeView,
    MemberViewSet,
    MyOrganizationsView,
)

router = SimpleRouter()
router.register(r'members', MemberViewSet, basename='org-members')

urlpatterns = [
    path('my/', MyOrganizationsView.as_view(), name='my_organizations'),
    path('current/', CurrentOrganizationView.as_view(), name='current_organization'),
    path('invites/', InviteCreateView.as_view(), name='invite_create'),
    path('invites/list/', InviteListView.as_view(), name='invite_list'),
    path('invites/<int:invite_id>/', InviteRevokeView.as_view(), name='invite_revoke'),
    path('', include(router.urls)),
]
