from rest_framework import permissions


def require_roles(*roles):
    """Фабрика разрешений для проверки одной из допустимых ролей"""
    class RolePermission(permissions.BasePermission):
        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            if request.user.is_superuser:
                return True
            user_roles = request.user.get_roles_for_org(getattr(request, 'org_id', None))
            return any(role in user_roles for role in roles)

    return RolePermission


class IsOrgAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return 'admin' in request.user.get_roles_for_org(getattr(request, 'org_id', None))


class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        roles = request.user.get_roles_for_org(getattr(request, 'org_id', None))
        return 'teacher' in roles or 'admin' in roles


class IsCurator(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = request.user.get_roles_for_org(getattr(request, 'org_id', None))
        return any(r in roles for r in ['curator', 'admin'])


class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = request.user.get_roles_for_org(getattr(request, 'org_id', None))
        return 'student' in roles


class IsParent(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = request.user.get_roles_for_org(getattr(request, 'org_id', None))
        return 'parent' in roles


class HasActiveEnrollmentOrPreview(permissions.BasePermission):
    """
    Разрешает доступ ученику только если у него есть активная запись на курс
    (status='active' и access_until не истек) ЛИБО если урок помечен is_free_preview.
    Учителя и админы курса имеют постоянный доступ.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        # Учителя и админы
        roles = user.get_roles_for_org(getattr(request, 'org_id', None))
        if 'admin' in roles or 'teacher' in roles or 'curator' in roles:
            return True

        # Бесплатный ознакомительный урок (free preview)
        is_preview = getattr(obj, 'is_free_preview', False)
        if hasattr(obj, 'lesson'):
            is_preview = is_preview or getattr(obj.lesson, 'is_free_preview', False)

        if is_preview:
            return True

        # Проверка активной записи ученика
        course_id = getattr(obj, 'course_id', None)
        if not course_id and hasattr(obj, 'section'):
            course_id = obj.section.course_id
        elif not course_id and hasattr(obj, 'lesson'):
            course_id = obj.lesson.section.course_id

        if not course_id:
            return False

        from django.utils import timezone

        from apps.courses.models import Enrollment

        return Enrollment.objects.filter(
            student=user,
            course_id=course_id,
            status='active',
            access_until__gte=timezone.now()
        ).exists()
