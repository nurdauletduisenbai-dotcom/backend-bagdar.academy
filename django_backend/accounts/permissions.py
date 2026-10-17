from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Кастомное разрешение: чтение доступно любому пользователю,
    а изменение и удаление — только автору/владельцу объекта.
    """
    def has_object_permission(self, request, view, obj):
        # Безопасные методы (GET, HEAD, OPTIONS) разрешены
        if request.method in permissions.SAFE_METHODS:
            return True

        # Проверка владельца объекта
        owner = getattr(obj, 'author', None) or getattr(obj, 'user', None) or getattr(obj, 'owner', None)
        if owner is not None:
            return owner == request.user or (request.user.is_authenticated and request.user.is_admin)

        return False


class IsAdminRole(permissions.BasePermission):
    """
    Разрешает доступ только пользователям с ролью ADMIN или статусом суперпользователя.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsModeratorOrAdminRole(permissions.BasePermission):
    """
    Разрешает доступ модераторам и администраторам.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_moderator
        )
