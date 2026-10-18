"""
Единые правила доступа к курсам и их содержимому.

- Управлять курсом (содержимое, задания, тесты, расписание): суперпользователь, админ организации курса,
  учитель — только если он в CourseStaff этого курса.
- Видеть содержимое курса: те, кто управляет, кураторы организации и ученики с активной записью.
- Родитель видит данные ребёнка, только если связь подтверждена.
"""
from django.db.models import Q
from django.utils import timezone

from .models import Course, CourseStaff, Enrollment


def org_roles(user, org_id) -> list[str]:
    if not user or not user.is_authenticated:
        return []
    return user.get_roles_for_org(org_id)


def is_org_admin(user, org_id) -> bool:
    return 'admin' in org_roles(user, org_id)


def is_org_staff(user, org_id) -> bool:
    return any(r in ('admin', 'teacher', 'curator') for r in org_roles(user, org_id))


def can_manage_course(user, course: Course) -> bool:
    roles = org_roles(user, course.org_id)
    if 'admin' in roles:
        return True
    return 'teacher' in roles and CourseStaff.objects.filter(course=course, teacher=user).exists()


def has_active_enrollment(user, course: Course) -> bool:
    if not user or not user.is_authenticated:
        return False
    return Enrollment.objects.filter(
        student=user, course=course, status=Enrollment.Status.ACTIVE, access_until__gte=timezone.now()
    ).exists()


def can_view_course_content(user, course: Course) -> bool:
    if can_manage_course(user, course):
        return True
    if 'curator' in org_roles(user, course.org_id):
        return True
    return has_active_enrollment(user, course)


def managed_course_ids(user, org_id=None):
    """ID курсов, которыми пользователь управляет (в текущей организации, если она задана)."""
    if user.is_superuser:
        qs = Course.objects.all()
        return qs.filter(org_id=org_id).values_list('id', flat=True) if org_id else qs.values_list('id', flat=True)
    admin_orgs = user.memberships.filter(is_active=True, role='admin').values_list('org_id', flat=True)
    qs = Course.objects.filter(Q(org_id__in=admin_orgs) | Q(staff__teacher=user))
    if org_id:
        qs = qs.filter(org_id=org_id)
    return qs.values_list('id', flat=True).distinct()


def viewable_course_ids(user, org_id=None):
    """ID курсов, содержимое которых пользователь может видеть."""
    if user.is_superuser:
        return managed_course_ids(user, org_id)
    curator_orgs = user.memberships.filter(is_active=True, role='curator').values_list('org_id', flat=True)
    qs = Course.objects.filter(
        Q(id__in=managed_course_ids(user))
        | Q(org_id__in=curator_orgs)
        | Q(
            enrollments__student=user,
            enrollments__status=Enrollment.Status.ACTIVE,
            enrollments__access_until__gte=timezone.now(),
        )
    )
    if org_id:
        qs = qs.filter(org_id=org_id)
    return qs.values_list('id', flat=True).distinct()


def active_student_ids(course: Course):
    return Enrollment.objects.filter(
        course=course, status=Enrollment.Status.ACTIVE, access_until__gte=timezone.now()
    ).values_list('student_id', flat=True)


def confirmed_children_ids(parent):
    from apps.accounts.models import ParentStudentRelation
    return ParentStudentRelation.objects.filter(parent=parent, is_confirmed=True).values_list('student_id', flat=True)


def can_view_student(viewer, student, org_id=None) -> bool:
    """Свои данные, данные ребёнка (подтверждённая связь) или персонал организации ученика."""
    if viewer.id == student.id or viewer.is_superuser:
        return True
    if student.id in set(confirmed_children_ids(viewer)):
        return True
    student_orgs = set(student.memberships.filter(is_active=True).values_list('org_id', flat=True))
    if org_id:
        student_orgs &= {org_id}
    return any(is_org_staff(viewer, o) for o in student_orgs)
