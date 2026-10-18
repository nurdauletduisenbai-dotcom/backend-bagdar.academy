from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError

from apps.courses.access import org_roles


class OrgScopedViewSet(viewsets.ModelViewSet):
    """
    Объекты, принадлежащие организации (темы, вопросы, объявления...).

    Видны и редактируются только в текущей организации (request.org_id) и только ролями
    из read_roles / write_roles. Без выбранной организации — 400.
    """
    permission_classes = [permissions.IsAuthenticated]
    org_path = 'org'
    read_roles: tuple[str, ...] = ('admin', 'teacher', 'curator')
    write_roles: tuple[str, ...] = ('admin', 'teacher')

    def require_org(self):
        org_id = getattr(self.request, 'org_id', None)
        if not org_id:
            raise ValidationError('Не выбрана организация: передайте заголовок X-Org-ID.')
        return org_id

    def roles(self):
        return org_roles(self.request.user, getattr(self.request, 'org_id', None))

    def check_permissions(self, request):
        super().check_permissions(request)
        if getattr(self, 'swagger_fake_view', False) or not request.user.is_authenticated:
            return
        self.require_org()
        needed = self.read_roles if request.method in permissions.SAFE_METHODS else self.write_roles
        if not any(r in needed for r in self.roles()):
            self.permission_denied(request, message='Недостаточно прав в этой организации.')

    def get_queryset(self):
        qs = self.queryset.all()
        if getattr(self, 'swagger_fake_view', False):
            return qs.none()
        return qs.filter(**{f'{self.org_path}_id': self.require_org()})
