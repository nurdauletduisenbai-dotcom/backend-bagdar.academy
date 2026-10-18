from django.urls import path

from .views import InviteCreateView, MyOrganizationsView

urlpatterns = [
    path('my/', MyOrganizationsView.as_view(), name='my_organizations'),
    path('invites/', InviteCreateView.as_view(), name='invite_create'),
]
