from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course
from .serializers import CourseListSerializer, CourseDetailSerializer


class CourseViewSet(viewsets.ModelViewSet):
    """
    Каталог курсов с многоарендной изоляцией организаций (Tenant Isolation).
    Публичные курсы доступны для просмотра ученикам и родителям.
    Создание и редактирование доступны учителям и администраторам.
    """
    queryset = Course.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'subject', 'grade_level', 'status']
    search_fields = ['title', 'description', 'subject']
    ordering_fields = ['created_at', 'price', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        org_id = getattr(self.request, 'org_id', None)
        if org_id:
            qs = qs.filter(org_id=org_id)

        # Не-персонал видит только опубликованные курсы
        user = self.request.user
        if not user.is_authenticated or not (user.is_staff or user.is_superuser):
            qs = qs.filter(status=Course.Status.PUBLISHED)
        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseListSerializer

    def perform_create(self, serializer):
        from apps.organizations.models import Organization
        org_id = getattr(self.request, 'org_id', None)
        org = Organization.objects.filter(id=org_id).first() if org_id else Organization.objects.first()
        serializer.save(created_by=self.request.user, org=org)
