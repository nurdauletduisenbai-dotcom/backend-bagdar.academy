from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RefreshToken
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RefreshTokenSerializer,
    RegisterByInviteSerializer,
    RegisterSerializer,
    SessionSerializer,
    UserProfileSerializer,
)
from .services import AuthService


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=RegisterSerializer, responses={201: UserProfileSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.register(**serializer.validated_data)
        return Response(
            {
                'message': 'Регистрация успешна. На ваш email отправлена ссылка для подтверждения.',
                'user': UserProfileSerializer(user, context={'request': request}).data
            },
            status=status.HTTP_201_CREATED
        )


class RegisterByInviteView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=RegisterByInviteSerializer)
    def post(self, request):
        serializer = RegisterByInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.register_by_invite(**serializer.validated_data)
        return Response(
            {
                'message': 'Регистрация по приглашению успешна.',
                'user': UserProfileSerializer(user, context={'request': request}).data
            },
            status=status.HTTP_201_CREATED
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = request.query_params.get('token')
        AuthService.verify_email(token)
        return Response({'message': 'Email успешно подтвержден.'})


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        device_info = request.META.get('HTTP_USER_AGENT', 'Browser')
        org_id = getattr(request, 'org_id', None)

        result = AuthService.login(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            ip=ip,
            device_info=device_info,
            org_id=org_id,
            totp_code=serializer.validated_data.get('totp_code')
        )

        response = Response(result, status=status.HTTP_200_OK)

        # Установка Refresh токена в безопасную HttpOnly Cookie
        if not result.get('requires_2fa') and 'refresh_token' in result:
            response.set_cookie(
                key='refresh_token',
                value=result['refresh_token'],
                max_age=30 * 24 * 3600,
                httponly=True,
                secure=not request.META.get('DEBUG', False),
                samesite='Lax',
                path='/api/v1/auth/'
            )
        return response


class RefreshTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=RefreshTokenSerializer)
    def post(self, request):
        raw_token = request.data.get('refresh') or request.COOKIES.get('refresh_token')
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        device_info = request.META.get('HTTP_USER_AGENT', '')

        result = AuthService.refresh_tokens(raw_token, ip, device_info)
        response = Response(result, status=status.HTTP_200_OK)

        # Обновляем cookie
        response.set_cookie(
            key='refresh_token',
            value=result['refresh_token'],
            max_age=30 * 24 * 3600,
            httponly=True,
            secure=True,
            samesite='Lax',
            path='/api/v1/auth/'
        )
        return response


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        raw_token = request.data.get('refresh') or request.COOKIES.get('refresh_token')
        AuthService.logout(raw_token)
        response = Response({'message': 'Сессия успешно завершена.'}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh_token', path='/api/v1/auth/')
        return response


class LogoutAllView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        AuthService.logout_all(request.user)
        response = Response({'message': 'Все активные сессии пользователя аннулированы.'}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh_token', path='/api/v1/auth/')
        return response


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({'error': {'code': 'invalid_password', 'message': 'Текущий пароль указан неверно.'}}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        # Отзываем все токены после смены пароля
        AuthService.logout_all(request.user)
        return Response({'message': 'Пароль успешно изменен. Войдите заново с новым паролем.'})


class ActiveSessionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        sessions = RefreshToken.objects.filter(user=request.user, revoked_at__isnull=True)
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)

    def delete(self, request, session_id):
        RefreshToken.objects.filter(id=session_id, user=request.user).update(revoked_at=timezone.now())
        return Response({'message': 'Сессия отозвана.'})
