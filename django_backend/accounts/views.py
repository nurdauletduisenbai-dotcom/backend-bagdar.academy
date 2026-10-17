from django.contrib.auth import get_user_model
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    LogoutSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Эндпоинт входа: принимает email и password, возвращает JWT Access и Refresh токены,
    а также данные пользователя.
    """
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    Эндпоинт регистрации нового пользователя.
    После успешной регистрации автоматически возвращает токены авторизации.
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    @extend_schema(
        responses={
            201: OpenApiResponse(description="Успешная регистрация с токенами")
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Генерация JWT токенов для нового пользователя
        refresh = RefreshToken.for_user(user)
        # Добавляем кастомные клеймы
        refresh['email'] = user.email
        refresh['role'] = user.role
        refresh['is_verified'] = user.is_verified

        return Response({
            'message': 'Пользователь успешно зарегистрирован',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Эндпоинт получения и редактирования профиля текущего авторизованного пользователя.
    Требует заголовок: Authorization: Bearer <access_token>
    """
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    """
    Эндпоинт смены пароля текущего пользователя.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response(
            {"detail": "Пароль успешно изменен."},
            status=status.HTTP_200_OK
        )


class LogoutView(generics.GenericAPIView):
    """
    Эндпоинт выхода из системы. Добавляет Refresh токен в Blacklist,
    делая его недействительным для последующих обновлений.
    """
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "Успешный выход из системы. Токен аннулирован."},
            status=status.HTTP_200_OK
        )
