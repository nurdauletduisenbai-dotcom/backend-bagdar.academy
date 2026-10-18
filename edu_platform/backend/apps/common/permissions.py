from rest_framework import permissions

STAFF_ROLES = ('admin', 'teacher', 'curator')


def user_roles(request):
    """Роли текущего пользователя в текущей организации (request.org_id)."""
    user = request.user
    if not user or not user.is_authenticated:
        return []
    return user.get_roles_for_org(getattr(request, 'org_id', None))


def require_roles(*roles):
    """Фабрика разрешений: пользователь должен иметь одну из ролей в текущей организации."""
    class RolePermission(permissions.BasePermission):
        message = 'Недостаточно прав для этого действия.'

        def has_permission(self, request, view):
            return any(role in user_roles(request) for role in roles)

    RolePermission.__name__ = f"Require{''.join(r.title() for r in roles)}"
    return RolePermission


IsOrgAdmin = require_roles('admin')
IsTeacher = require_roles('teacher', 'admin')
IsCurator = require_roles('curator', 'admin')
IsOrgStaff = require_roles(*STAFF_ROLES)
IsStudent = require_roles('student')
IsParent = require_roles('parent')


class IsOrgStaffOrReadOnly(permissions.BasePermission):
    """Чтение — всем, изменение — учителям/кураторам/админам текущей организации."""
    message = 'Изменять данные могут только учителя и администраторы организации.'

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return any(role in user_roles(request) for role in ('admin', 'teacher'))
