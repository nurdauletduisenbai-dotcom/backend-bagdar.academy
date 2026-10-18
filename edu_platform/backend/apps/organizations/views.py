import secrets

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.services import hash_token
from apps.audit.services import AuditService
from apps.common.permissions import user_roles

from .models import Invite, Organization, OrgMembership
from .serializers import (
    AddMemberSerializer,
    InviteCreatedSerializer,
    InviteCreateSerializer,
    InviteListSerializer,
    MemberSerializer,
    MyOrganizationSerializer,
    OrganizationSerializer,
)


@extend_schema(tags=['organizations'])
class MyOrganizationsView(generics.ListAPIView):
    """Организации, в которых состоит пользователь (для выбора X-Org-ID на фронтенде)."""
    serializer_class = MyOrganizationSerializer
    pagination_class = None
    queryset = Organization.objects.none()

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Organization.objects.none()
        user = self.request.user
        if user.is_superuser:
            return Organization.objects.filter(is_active=True)
        return Organization.objects.filter(
            is_active=True, memberships__user=user, memberships__is_active=True
        ).distinct()


@extend_schema(tags=['organizations'])
class InviteCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary='Создать приглашение в текущую организацию',
        description=(
            'Админ приглашает любую роль. Учитель — только учеников и только на курс своей организации. '
            'Токен приглашения возвращается один раз; регистрация — POST /api/v1/auth/register-by-invite/.'
        ),
        request=InviteCreateSerializer,
        responses={201: InviteCreatedSerializer},
    )
    def post(self, request):
        org_id = getattr(request, 'org_id', None)
        if not org_id:
            raise ValidationError('Не выбрана организация: передайте заголовок X-Org-ID.')

        serializer = InviteCreateSerializer(data=request.data, context={'org_id': org_id})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        roles = user_roles(request)
        is_admin = 'admin' in roles
        is_teacher_inviting_student = 'teacher' in roles and data['role'] == 'student' and data['course']
        if not (is_admin or is_teacher_inviting_student):
            raise PermissionDenied('Учитель может приглашать только учеников на курс; остальные роли — администратор.')

        raw_token = secrets.token_urlsafe(32)
        invite = Invite.objects.create(
            org_id=org_id,
            role=data['role'],
            course=data['course'],
            group=data['group'],
            max_uses=data['max_uses'],
            expires_at=data['expires_at'],
            token_hash=hash_token(raw_token),
            created_by=request.user,
        )
        invite.invite_token = raw_token
        return Response(InviteCreatedSerializer(invite).data, status=status.HTTP_201_CREATED)


def _require_admin(request):
    org_id = getattr(request, 'org_id', None)
    if not org_id:
        raise ValidationError('Не выбрана организация: передайте заголовок X-Org-ID.')
    if 'admin' not in user_roles(request):
        raise PermissionDenied('Действие доступно администратору организации.')
    return org_id


@extend_schema(tags=['organizations'])
class CurrentOrganizationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Текущая организация', responses=OrganizationSerializer)
    def get(self, request):
        org_id = getattr(request, 'org_id', None)
        if not org_id:
            raise ValidationError('Не выбрана организация: передайте заголовок X-Org-ID.')
        return Response(OrganizationSerializer(get_object_or_404(Organization, id=org_id)).data)

    @extend_schema(summary='Изменить настройки организации (админ)', request=OrganizationSerializer,
                   responses=OrganizationSerializer)
    def patch(self, request):
        org = get_object_or_404(Organization, id=_require_admin(request))
        serializer = OrganizationSerializer(org, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary='Участники организации (персонал)',
                       parameters=[OpenApiParameter('role', str), OpenApiParameter('is_active', bool),
                                   OpenApiParameter('search', str)]),
    partial_update=extend_schema(summary='Изменить роль или отключить участника (админ)'),
    destroy=extend_schema(summary='Отключить участника (админ)'),
)
@extend_schema(tags=['organizations'])
class MemberViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['role', 'is_active']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return OrgMembership.objects.none()
        org_id = getattr(self.request, 'org_id', None)
        if not org_id:
            raise ValidationError('Не выбрана организация: передайте заголовок X-Org-ID.')
        if not any(r in ('admin', 'teacher', 'curator') for r in user_roles(self.request)):
            raise PermissionDenied('Список участников доступен персоналу.')
        return OrgMembership.objects.filter(org_id=org_id).select_related('user').order_by('role', 'user__email')

    def _guard_last_admin(self, membership, new_role=None, new_active=True):
        losing_admin = membership.role == 'admin' and (new_role not in (None, 'admin') or not new_active)
        if losing_admin and not OrgMembership.objects.filter(
            org_id=membership.org_id, role='admin', is_active=True
        ).exclude(id=membership.id).exists():
            raise ValidationError('Нельзя убрать последнего администратора организации.')

    def perform_update(self, serializer):
        _require_admin(self.request)
        m = serializer.instance
        new_role = serializer.validated_data.get('role', m.role)
        new_active = serializer.validated_data.get('is_active', m.is_active)
        self._guard_last_admin(m, new_role, new_active)
        if new_role != m.role and OrgMembership.objects.filter(org_id=m.org_id, user_id=m.user_id, role=new_role).exclude(id=m.id).exists():
            raise ValidationError({'role': 'У пользователя уже есть эта роль.'})
        old = {'role': m.role, 'is_active': m.is_active}
        serializer.save()
        AuditService.log(AuditService.Action.ROLE_CHANGE, user=self.request.user, request=self.request, entity=m,
                         changes={'before': old, 'after': {'role': new_role, 'is_active': new_active},
                                  'member_user_id': m.user_id})

    def perform_destroy(self, instance):
        _require_admin(self.request)
        self._guard_last_admin(instance, new_active=False)
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])
        AuditService.log(AuditService.Action.MEMBER_DEACTIVATE, user=self.request.user, request=self.request,
                         entity=instance, changes={'member_user_id': instance.user_id})

    @extend_schema(summary='Добавить существующего пользователя в организацию (админ)', request=AddMemberSerializer,
                   responses={201: MemberSerializer})
    def create(self, request):
        org_id = _require_admin(request)
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from apps.accounts.models import User
        user = User.objects.filter(email=serializer.validated_data['email'].lower()).first()
        if not user:
            raise ValidationError({'email': 'Пользователь не найден — отправьте ему приглашение.'})
        membership, created = OrgMembership.objects.get_or_create(
            org_id=org_id, user=user, role=serializer.validated_data['role'], defaults={'is_active': True}
        )
        if not created and not membership.is_active:
            membership.is_active = True
            membership.save(update_fields=['is_active', 'updated_at'])
        AuditService.log(AuditService.Action.ROLE_CHANGE, user=request.user, request=request, entity=membership,
                         changes={'added': membership.role, 'member_user_id': user.id})
        return Response(MemberSerializer(membership).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['organizations'])
class InviteListView(generics.ListAPIView):
    serializer_class = InviteListSerializer

    @extend_schema(summary='Приглашения организации (админ)')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Invite.objects.none()
        return Invite.objects.filter(org_id=_require_admin(self.request)).order_by('-created_at')


@extend_schema(tags=['organizations'])
class InviteRevokeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Отозвать приглашение (админ)', responses={204: None})
    def delete(self, request, invite_id):
        invite = get_object_or_404(Invite, id=invite_id, org_id=_require_admin(request))
        invite.expires_at = timezone.now()
        invite.save(update_fields=['expires_at', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)
