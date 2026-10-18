from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, serializers, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.courses.access import is_org_admin

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)

    class Meta:
        model = AuditLog
        fields = ('id', 'created_at', 'action', 'user', 'user_email', 'ip_address', 'request_id', 'entity_type',
                  'entity_id', 'changes')
        read_only_fields = fields


@extend_schema_view(list=extend_schema(
    summary='Журнал аудита организации (админ)',
    parameters=[OpenApiParameter('action', str), OpenApiParameter('user', int),
                OpenApiParameter('date_from', str), OpenApiParameter('date_to', str)],
))
@extend_schema(tags=['audit'])
class AuditLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['action', 'user', 'entity_type']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AuditLog.objects.none()
        org_id = getattr(self.request, 'org_id', None)
        if not org_id:
            raise ValidationError('Не выбрана организация: передайте заголовок X-Org-ID.')
        if not is_org_admin(self.request.user, org_id):
            raise PermissionDenied('Журнал аудита доступен администратору.')
        qs = AuditLog.objects.filter(org_id=org_id).select_related('user')
        params = self.request.query_params
        if params.get('date_from') and parse_datetime(params['date_from']):
            qs = qs.filter(created_at__gte=parse_datetime(params['date_from']))
        if params.get('date_to') and parse_datetime(params['date_to']):
            qs = qs.filter(created_at__lte=parse_datetime(params['date_to']))
        return qs
