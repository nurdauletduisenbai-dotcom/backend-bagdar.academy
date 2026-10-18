from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework_simplejwt.authentication import JWTAuthentication

from .tenancy import resolve_org_id


class TenantJWTAuthentication(JWTAuthentication):
    """
    JWT-аутентификация + определение текущей организации (request.org_id).

    Middleware не видит JWT-пользователя (DRF аутентифицирует позже, во view),
    поэтому организация проверяется здесь: заголовок X-Org-ID важнее org_id из токена,
    и пользователь обязан состоять в выбранной организации.
    """

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None

        user, token = result
        requested = getattr(request._request, 'org_id', None) or token.get('org_id')
        request._request.org_id = resolve_org_id(user, requested)
        return user, token


class TenantJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """Описание схемы Bearer JWT для Swagger (кнопка Authorize)."""

    target_class = 'apps.common.authentication.TenantJWTAuthentication'
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Access-токен из POST /api/v1/auth/login/ (поле access_token).',
        }
