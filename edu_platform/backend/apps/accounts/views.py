from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.audit.services import AuditService
from apps.common.serializers import MessageSerializer

from .models import ParentStudentRelation, RefreshToken
from .serializers import (
    ChangePasswordSerializer,
    EmailSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    LogoutSerializer,
    ParentLinkRequestSerializer,
    ParentRelationSerializer,
    PasswordResetConfirmSerializer,
    RefreshTokenSerializer,
    RegisterByInviteSerializer,
    RegisterResponseSerializer,
    RegisterSerializer,
    SessionSerializer,
    TokenPairSerializer,
    TwoFactorBackupCodesSerializer,
    TwoFactorCodeSerializer,
    TwoFactorDisableSerializer,
    TwoFactorSetupResponseSerializer,
    UserProfileSerializer,
)
from .services import AuthService, ParentService, TwoFactorService

REFRESH_COOKIE = 'refresh_token'
REFRESH_COOKIE_PATH = '/api/v1/auth/'


def _client_ip(request) -> str:
    return request.META.get('REMOTE_ADDR') or '127.0.0.1'


def _set_refresh_cookie(response, raw_token: str):
    """Refresh-токен в HttpOnly cookie, доступной только эндпоинтам /api/v1/auth/."""
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_token,
        max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        path=REFRESH_COOKIE_PATH,
    )


def _incoming_refresh(request) -> str | None:
    return request.data.get('refresh') or request.COOKIES.get(REFRESH_COOKIE)


class PublicAuthView(APIView):
    """
    Публичный auth-эндпоинт: без проверки access-токена (он может быть истёкшим).
    Заголовок WWW-Authenticate нужен, чтобы ошибки входа отдавались как 401, а не 403.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get_authenticate_header(self, request):
        return 'Bearer realm="api"'


class AuthThrottledView(PublicAuthView):
    """Публичные auth-эндпоинты с ограничением частоты запросов."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'


@extend_schema(tags=['auth'])
class RegisterView(AuthThrottledView):
    @extend_schema(
        summary='Регистрация ученика или родителя',
        request=RegisterSerializer,
        responses={201: RegisterResponseSerializer},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.register(**serializer.validated_data)
        return Response(
            {
                'message': 'Регистрация успешна. На ваш email отправлена ссылка для подтверждения.',
                'user': UserProfileSerializer(user, context={'request': request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=['auth'])
class RegisterByInviteView(AuthThrottledView):
    @extend_schema(
        summary='Регистрация по приглашению (учитель, куратор, ученик курса)',
        request=RegisterByInviteSerializer,
        responses={201: RegisterResponseSerializer},
    )
    def post(self, request):
        serializer = RegisterByInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.register_by_invite(**serializer.validated_data)
        return Response(
            {
                'message': 'Регистрация по приглашению успешна.',
                'user': UserProfileSerializer(user, context={'request': request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=['auth'])
class VerifyEmailView(AuthThrottledView):
    @extend_schema(
        summary='Подтверждение email по ссылке из письма',
        parameters=[OpenApiParameter('token', str, required=True)],
        responses={200: MessageSerializer},
    )
    def get(self, request):
        AuthService.verify_email(request.query_params.get('token'))
        return Response({'message': 'Email успешно подтвержден.'})


@extend_schema(tags=['auth'])
class LoginView(AuthThrottledView):
    @extend_schema(
        summary='Вход: access-токен в ответе, refresh-токен в ответе и в HttpOnly cookie',
        description=(
            'Если у пользователя включена 2FA и код не передан, возвращается `{"requires_2fa": true}` — '
            'повторите запрос с `totp_code`. Организация берётся из заголовка `X-Org-ID`, '
            'либо выбирается автоматически, если пользователь состоит в одной организации.'
        ),
        request=LoginSerializer,
        responses={200: LoginResponseSerializer},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = AuthService.login(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            ip=_client_ip(request),
            device_info=request.META.get('HTTP_USER_AGENT', ''),
            org_id=getattr(request, 'org_id', None),
            totp_code=serializer.validated_data.get('totp_code'),
        )
        response = Response(result, status=status.HTTP_200_OK)
        if not result['requires_2fa']:
            _set_refresh_cookie(response, result['refresh_token'])
        return response


@extend_schema(tags=['auth'])
class RefreshTokenView(AuthThrottledView):
    throttle_scope = 'auth_refresh'

    @extend_schema(
        summary='Обновление токенов (ротация refresh-токена)',
        description='Повторное использование уже заменённого refresh-токена отзывает все сессии пользователя.',
        request=RefreshTokenSerializer,
        responses={200: TokenPairSerializer},
    )
    def post(self, request):
        result = AuthService.refresh_tokens(
            _incoming_refresh(request),
            ip=_client_ip(request),
            device_info=request.META.get('HTTP_USER_AGENT', ''),
            org_id=getattr(request, 'org_id', None),
        )
        response = Response(result, status=status.HTTP_200_OK)
        _set_refresh_cookie(response, result['refresh_token'])
        return response


@extend_schema(tags=['auth'])
class LogoutView(PublicAuthView):
    # Выход должен работать и с истёкшим access-токеном — достаточно refresh-токена

    @extend_schema(summary='Выход из текущей сессии', request=LogoutSerializer, responses={200: MessageSerializer})
    def post(self, request):
        AuthService.logout(_incoming_refresh(request))
        response = Response({'message': 'Сессия успешно завершена.'}, status=status.HTTP_200_OK)
        response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
        return response


@extend_schema(tags=['auth'])
class LogoutAllView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Выход со всех устройств', request=None, responses={200: MessageSerializer})
    def post(self, request):
        AuthService.logout_all(request.user)
        AuditService.log(AuditService.Action.LOGOUT, user=request.user, request=request, changes={'all': True})
        response = Response({'message': 'Все активные сессии пользователя аннулированы.'}, status=status.HTTP_200_OK)
        response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
        return response


@extend_schema(tags=['users'])
class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Профиль текущего пользователя', responses={200: UserProfileSerializer})
    def get(self, request):
        return Response(UserProfileSerializer(request.user, context={'request': request}).data)

    @extend_schema(summary='Изменение профиля', request=UserProfileSerializer, responses={200: UserProfileSerializer})
    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema(tags=['auth'])
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Смена пароля (завершает все сессии)', request=ChangePasswordSerializer,
                   responses={200: MessageSerializer})
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': {'code': 'invalid_password', 'message': 'Текущий пароль указан неверно.', 'details': {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        # Access-токены перестают действовать сразу (CHECK_REVOKE_TOKEN), refresh-сессии отзываем
        AuthService.logout_all(request.user)
        AuditService.log(AuditService.Action.PASSWORD_CHANGE, user=request.user, request=request)
        response = Response({'message': 'Пароль успешно изменен. Войдите заново с новым паролем.'})
        response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
        return response


@extend_schema(tags=['auth'])
class ActiveSessionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Активные сессии (устройства)', responses={200: SessionSerializer(many=True)})
    def get(self, request):
        sessions = RefreshToken.objects.filter(
            user=request.user, revoked_at__isnull=True, expires_at__gt=timezone.now()
        )
        serializer = SessionSerializer(sessions, many=True, context={'current_refresh': _incoming_refresh(request)})
        return Response(serializer.data)


@extend_schema(tags=['auth'])
class SessionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Завершить сессию на другом устройстве', responses={200: MessageSerializer})
    def delete(self, request, session_id):
        session = get_object_or_404(RefreshToken, id=session_id, user=request.user, revoked_at__isnull=True)
        session.revoked_at = timezone.now()
        session.save(update_fields=['revoked_at'])
        return Response({'message': 'Сессия отозвана.'})


@extend_schema(tags=['2fa'])
class TwoFactorSetupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Шаг 1: получить секрет и otpauth-ссылку для QR-кода', request=None,
                   responses={200: TwoFactorSetupResponseSerializer})
    def post(self, request):
        return Response(TwoFactorService.setup(request.user))


@extend_schema(tags=['2fa'])
class TwoFactorEnableView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Шаг 2: подтвердить кодом и включить 2FA (выдаёт резервные коды)',
                   request=TwoFactorCodeSerializer, responses={200: TwoFactorBackupCodesSerializer})
    def post(self, request):
        serializer = TwoFactorCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        codes = TwoFactorService.enable(request.user, serializer.validated_data['code'])
        return Response({'message': '2FA включена. Сохраните резервные коды.', 'backup_codes': codes})


@extend_schema(tags=['2fa'])
class TwoFactorDisableView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Отключить 2FA (нужны пароль и код)', request=TwoFactorDisableSerializer,
                   responses={200: MessageSerializer})
    def post(self, request):
        serializer = TwoFactorDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        TwoFactorService.disable(request.user, **serializer.validated_data)
        return Response({'message': '2FA отключена.'})


@extend_schema(tags=['auth'])
class ResendVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Отправить письмо подтверждения ещё раз', request=None, responses={200: MessageSerializer})
    def post(self, request):
        AuthService.resend_verification(request.user)
        return Response({'message': 'Письмо отправлено.'})


@extend_schema(tags=['auth'])
class PasswordResetRequestView(AuthThrottledView):
    @extend_schema(summary='Запросить сброс пароля (письмо со ссылкой)', request=EmailSerializer,
                   responses={200: MessageSerializer})
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.request_password_reset(serializer.validated_data['email'])
        return Response({'message': 'Если такой email зарегистрирован, мы отправили на него ссылку для сброса.'})


@extend_schema(tags=['auth'])
class PasswordResetConfirmView(AuthThrottledView):
    @extend_schema(summary='Задать новый пароль по токену из письма', request=PasswordResetConfirmSerializer,
                   responses={200: MessageSerializer})
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.reset_password(serializer.validated_data['token'], serializer.validated_data['new_password'])
        return Response({'message': 'Пароль изменён. Войдите с новым паролем.'})


@extend_schema(tags=['parents'])
class ParentChildrenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Мои дети (родитель)', responses=ParentRelationSerializer(many=True))
    def get(self, request):
        relations = ParentStudentRelation.objects.filter(parent=request.user).select_related('parent', 'student')
        return Response(ParentRelationSerializer(relations, many=True).data)

    @extend_schema(summary='Запросить привязку ребёнка по email (ребёнок подтверждает)',
                   request=ParentLinkRequestSerializer, responses={201: ParentRelationSerializer})
    def post(self, request):
        serializer = ParentLinkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        relation = ParentService.request_link(request.user, serializer.validated_data['student_email'])
        return Response(ParentRelationSerializer(relation).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['parents'])
class ParentChildDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Отвязать ребёнка', responses={204: None})
    def delete(self, request, relation_id):
        get_object_or_404(ParentStudentRelation, id=relation_id, parent=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['parents'])
class ParentRequestsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Запросы от родителей (ученик)', responses=ParentRelationSerializer(many=True))
    def get(self, request):
        relations = ParentStudentRelation.objects.filter(student=request.user).select_related('parent', 'student')
        return Response(ParentRelationSerializer(relations, many=True).data)


@extend_schema(tags=['parents'])
class ParentRequestDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Подтвердить запрос родителя', request=None, responses=ParentRelationSerializer)
    def post(self, request, relation_id):
        relation = get_object_or_404(ParentStudentRelation, id=relation_id, student=request.user)
        relation.is_confirmed = True
        relation.save(update_fields=['is_confirmed', 'updated_at'])
        return Response(ParentRelationSerializer(relation).data)

    @extend_schema(summary='Отклонить / отозвать доступ родителя', responses={204: None})
    def delete(self, request, relation_id):
        get_object_or_404(ParentStudentRelation, id=relation_id, student=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
