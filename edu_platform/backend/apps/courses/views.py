from datetime import timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.audit.services import AuditService
from apps.common.permissions import STAFF_ROLES, IsOrgStaff, IsOrgStaffOrReadOnly, user_roles

from .models import Course, CourseStaff, Enrollment, Group
from .serializers import CourseDetailSerializer, CourseListSerializer, EnrollmentSerializer, EnrollStudentSerializer

ORG_HEADER = OpenApiParameter(
    'X-Org-ID', int, OpenApiParameter.HEADER, required=False,
    description='ID организации. Обязателен для изменения данных, если пользователь состоит в нескольких.',
)


@extend_schema_view(
    list=extend_schema(summary='Каталог курсов', parameters=[ORG_HEADER]),
    retrieve=extend_schema(summary='Курс: разделы, уроки, видео, тесты', parameters=[ORG_HEADER]),
    create=extend_schema(summary='Создать курс (учитель/админ)', parameters=[ORG_HEADER]),
    update=extend_schema(summary='Изменить курс', parameters=[ORG_HEADER]),
    partial_update=extend_schema(summary='Частично изменить курс', parameters=[ORG_HEADER]),
    destroy=extend_schema(summary='Удалить курс (мягкое удаление)', parameters=[ORG_HEADER]),
)
@extend_schema(tags=['courses'])
class CourseViewSet(viewsets.ModelViewSet):
    """
    Каталог курсов с изоляцией организаций.
    - Гости и ученики видят только опубликованные курсы.
    - Персонал организации (админ/учитель/куратор) видит и черновики своей организации.
    - Создавать курсы могут учителя и админы; изменять/удалять — админ или преподаватель курса.
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'subject', 'grade_level', 'status']
    search_fields = ['title', 'description', 'subject']
    ordering_fields = ['created_at', 'price', 'title']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        if self.action in ('my',):
            return [permissions.IsAuthenticated()]
        if self.action in ('enroll_student', 'enrollments'):
            return [permissions.IsAuthenticated(), IsOrgStaff()]
        return [permissions.IsAuthenticated(), IsOrgStaffOrReadOnly()]

    def get_queryset(self):
        qs = Course.objects.select_related('org')
        org_id = getattr(self.request, 'org_id', None)
        user = self.request.user

        if org_id:
            qs = qs.filter(org_id=org_id)
            is_staff = any(r in STAFF_ROLES for r in user_roles(self.request))
            return qs if is_staff else qs.filter(status=Course.Status.PUBLISHED)

        # Организация не выбрана: публичный каталог опубликованных курсов.
        # Пользователь, состоящий в организациях, видит только их курсы.
        qs = qs.filter(status=Course.Status.PUBLISHED, org__is_active=True)
        if user.is_authenticated and not user.is_superuser:
            org_ids = user.memberships.filter(is_active=True).values_list('org_id', flat=True)
            qs = qs.filter(Q(org_id__in=org_ids))
        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailSerializer
        if self.action == 'enroll_student':
            return EnrollStudentSerializer
        if self.action == 'enrollments':
            return EnrollmentSerializer
        return CourseListSerializer

    def _require_org(self):
        org_id = getattr(self.request, 'org_id', None)
        if not org_id:
            raise ValidationError('Не выбрана организация: передайте заголовок X-Org-ID.')
        return org_id

    def _check_can_manage(self, course: Course):
        roles = self.request.user.get_roles_for_org(course.org_id)
        if 'admin' in roles:
            return
        if 'teacher' in roles and CourseStaff.objects.filter(course=course, teacher=self.request.user).exists():
            return
        raise PermissionDenied('Изменять курс может администратор или преподаватель этого курса.')

    def perform_create(self, serializer):
        org_id = self._require_org()
        course = serializer.save(created_by=self.request.user, org_id=org_id)
        CourseStaff.objects.get_or_create(course=course, teacher=self.request.user)
        AuditService.log(AuditService.Action.COURSE_CREATE, user=self.request.user, request=self.request, entity=course)

    def perform_update(self, serializer):
        self._check_can_manage(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_can_manage(instance)
        AuditService.log(AuditService.Action.COURSE_DELETE, user=self.request.user, request=self.request, entity=instance)
        instance.delete()

    @extend_schema(summary='Мои курсы (активные записи текущего пользователя)', responses=CourseListSerializer(many=True))
    @action(detail=False, methods=['get'])
    def my(self, request):
        qs = Course.objects.filter(
            enrollments__student=request.user,
            enrollments__status=Enrollment.Status.ACTIVE,
            enrollments__access_until__gte=timezone.now(),
        ).distinct()
        if getattr(request, 'org_id', None):
            qs = qs.filter(org_id=request.org_id)
        page = self.paginate_queryset(qs.order_by('-created_at'))
        return self.get_paginated_response(CourseListSerializer(page, many=True, context={'request': request}).data)

    @extend_schema(
        summary='Записать ученика на курс (персонал организации)',
        parameters=[ORG_HEADER],
        request=EnrollStudentSerializer,
        responses={201: EnrollmentSerializer},
    )
    @action(detail=True, methods=['post'], url_path='enroll-student')
    def enroll_student(self, request, pk=None):
        course = self.get_object()
        serializer = EnrollStudentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from apps.accounts.models import User
        student = User.objects.filter(
            email=data['student_email'].lower(),
            memberships__org_id=course.org_id,
            memberships__role='student',
            memberships__is_active=True,
        ).first()
        if not student:
            raise ValidationError({'student_email': 'Ученик с таким email не найден в этой организации.'})

        group = None
        if data.get('group_id'):
            group = get_object_or_404(Group, id=data['group_id'], course=course)

        enrollment, _ = Enrollment.objects.update_or_create(
            course=course,
            student=student,
            defaults={
                'group': group,
                'status': Enrollment.Status.ACTIVE,
                'access_until': timezone.now() + timedelta(days=data['access_days']),
            },
        )
        return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)

    @extend_schema(summary='Записи на курс (персонал организации)', parameters=[ORG_HEADER])
    @action(detail=True, methods=['get'])
    def enrollments(self, request, pk=None):
        course = self.get_object()
        qs = Enrollment.objects.filter(course=course).select_related('student').order_by('-enrolled_at')
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(EnrollmentSerializer(page, many=True).data)
