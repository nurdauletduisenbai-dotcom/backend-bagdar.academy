from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.access import (
    can_manage_course,
    can_view_student,
    confirmed_children_ids,
    is_org_admin,
    is_org_staff,
)
from apps.courses.models import Course, Enrollment

from .models import CourseProgress
from .services import ProgressService

User = get_user_model()
REPORT = OpenApiResponse(description='Отчёт: уроки, тесты, задания, посещаемость')


def _summary(enrollment: Enrollment) -> dict:
    progress = ProgressService.recalculate(enrollment.student, enrollment.course)
    return {
        'course_id': enrollment.course_id,
        'course_title': enrollment.course.title,
        'enrollment_status': enrollment.status,
        'access_until': enrollment.access_until,
        'percent_completed': progress.percent_completed if progress else 0.0,
        'average_test_score': progress.average_test_score if progress else 0.0,
    }


@extend_schema(tags=['progress'])
class MyProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Мой прогресс по всем курсам', responses=REPORT)
    def get(self, request):
        enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
        return Response([_summary(e) for e in enrollments])


@extend_schema(tags=['progress'])
class StudentProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Прогресс ученика по всем курсам (родитель или персонал)', responses=REPORT)
    def get(self, request, student_id):
        student = get_object_or_404(User, id=student_id)
        if not can_view_student(request.user, student, getattr(request, 'org_id', None)):
            raise PermissionDenied('Нет доступа к данным этого ученика.')
        enrollments = Enrollment.objects.filter(student=student).select_related('course')
        if request.user.id != student.id and student.id not in _children(request.user):
            # Персонал видит только курсы своих организаций
            enrollments = [e for e in enrollments if is_org_staff(request.user, e.course.org_id)]
        return Response({'student_id': student.id, 'full_name': student.get_full_name(),
                         'courses': [_summary(e) for e in enrollments]})


def _children(user):
    return set(confirmed_children_ids(user))


@extend_schema(tags=['progress'])
class CourseProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Подробный прогресс по курсу (свой; родитель/персонал — с ?student=ID)',
        parameters=[OpenApiParameter('student', int)],
        responses=REPORT,
    )
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        student = request.user
        student_id = request.query_params.get('student')
        if student_id:
            if not student_id.isdigit():
                raise ValidationError({'student': 'Ожидается ID.'})
            student = get_object_or_404(User, id=student_id)
            allowed = (student.id == request.user.id or int(student_id) in _children(request.user)
                       or is_org_staff(request.user, course.org_id))
            if not allowed:
                raise PermissionDenied('Нет доступа к данным этого ученика.')
        if not Enrollment.objects.filter(student=student, course=course).exists():
            raise ValidationError('Ученик не записан на этот курс.')
        return Response(ProgressService.course_report(student, course))


@extend_schema(tags=['progress'])
class CourseStudentsProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Прогресс всех учеников курса (преподаватель)', responses=REPORT)
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        is_curator = 'curator' in request.user.get_roles_for_org(course.org_id)
        if not (can_manage_course(request.user, course) or is_curator):
            raise PermissionDenied('Доступно преподавателю курса, куратору или админу.')
        return Response(ProgressService.course_students_table(course))


@extend_schema(tags=['progress'])
class OrgSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Сводка по организации (админ): ученики, курсы, выручка, прогресс', responses=REPORT)
    def get(self, request):
        org_id = getattr(request, 'org_id', None)
        if not org_id:
            raise ValidationError('Не выбрана организация: передайте заголовок X-Org-ID.')
        if not is_org_admin(request.user, org_id):
            raise PermissionDenied('Сводка доступна администратору организации.')

        from apps.organizations.models import OrgMembership
        from apps.payments.models import Order

        now = timezone.now()
        members = dict(
            OrgMembership.objects.filter(org_id=org_id, is_active=True)
            .values('role').annotate(n=Count('id')).values_list('role', 'n')
        )
        courses = dict(
            Course.objects.filter(org_id=org_id).values('status').annotate(n=Count('id')).values_list('status', 'n')
        )
        active_enrollments = Enrollment.objects.filter(
            course__org_id=org_id, status=Enrollment.Status.ACTIVE, access_until__gte=now
        ).count()
        month_ago = now - timezone.timedelta(days=30)
        paid = Order.objects.filter(course__org_id=org_id, status=Order.Status.PAID)
        return Response({
            'members_by_role': members,
            'courses_by_status': courses,
            'active_enrollments': active_enrollments,
            'average_progress_pct': round(
                CourseProgress.objects.filter(enrollment__course__org_id=org_id)
                .aggregate(v=Avg('percent_completed'))['v'] or 0.0, 1),
            'revenue_total': paid.aggregate(v=Sum('amount'))['v'] or 0,
            'revenue_30d': paid.filter(paid_at__gte=month_ago).aggregate(v=Sum('amount'))['v'] or 0,
            'orders_pending': Order.objects.filter(course__org_id=org_id, status=Order.Status.PENDING).count(),
        })
