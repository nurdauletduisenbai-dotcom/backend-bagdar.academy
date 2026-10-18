from django.urls import path

from .views import ParentChildDetailView, ParentChildrenView, ParentRequestDetailView, ParentRequestsView

urlpatterns = [
    path('children/', ParentChildrenView.as_view(), name='parent_children'),
    path('children/<int:relation_id>/', ParentChildDetailView.as_view(), name='parent_child_detail'),
    path('requests/', ParentRequestsView.as_view(), name='parent_requests'),
    path('requests/<int:relation_id>/', ParentRequestDetailView.as_view(), name='parent_request_detail'),
]
