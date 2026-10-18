"""
URL configuration for the Django backend.
Includes JWT Auth routes, Core API routes, and Swagger / OpenAPI documentation.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Django Admin Panel
    path('admin/', admin.site.urls),

    # Authentication & JWT Endpoints (/api/v1/auth/...)
    path('api/v1/auth/', include('accounts.urls')),

    # Core Business Domain Endpoints (/api/v1/...)
    path('api/v1/', include('core_api.urls')),

    # OpenAPI 3 Schema & Swagger / Redoc UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
