import secrets

from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.services import hash_token
from apps.common.permissions import user_roles

from .models import Invite, Organization
from .serializers import InviteCreatedSerializer, InviteCreateSerializer, MyOrganizationSerializer


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
