from django.urls import path
from .views import (
    RegisterView,
    RegisterByInviteView,
    VerifyEmailView,
    LoginView,
    RefreshTokenView,
    LogoutView,
    LogoutAllView,
    UserProfileView,
    ChangePasswordView,
    ActiveSessionsView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('register-by-invite/', RegisterByInviteView.as_view(), name='auth_register_by_invite'),
    path('verify-email/', VerifyEmailView.as_view(), name='auth_verify_email'),
    path('login/', LoginView.as_view(), name='auth_login'),
    path('refresh/', RefreshTokenView.as_view(), name='auth_refresh'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('logout-all/', LogoutAllView.as_view(), name='auth_logout_all'),
    path('change-password/', ChangePasswordView.as_view(), name='auth_change_password'),
    path('sessions/', ActiveSessionsView.as_view(), name='auth_sessions'),
    path('sessions/<int:session_id>/', ActiveSessionsView.as_view(), name='auth_session_detail'),
    path('users/me/', UserProfileView.as_view(), name='user_me'),
]
