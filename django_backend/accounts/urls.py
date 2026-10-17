from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    UserProfileView,
    ChangePasswordView,
    LogoutView,
)

urlpatterns = [
    # Получение JWT токенов (логин)
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # Обновление истекшего Access токена с помощью Refresh токена
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Проверка валидности любого JWT токена
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Регистрация нового пользователя
    path('register/', RegisterView.as_view(), name='auth_register'),

    # Профиль текущего пользователя (GET / PATCH / PUT)
    path('profile/', UserProfileView.as_view(), name='user_profile'),

    # Смена пароля
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),

    # Выход из системы (Blacklist refresh token)
    path('logout/', LogoutView.as_view(), name='auth_logout'),
]
