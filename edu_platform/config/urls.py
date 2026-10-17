from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


def health_check(request):
    return JsonResponse({'status': 'healthy', 'service': 'edu_platform_api'})


def ready_check(request):
    from django.db import connection
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    return JsonResponse({
        'status': 'ready' if db_ok else 'not_ready',
        'database': 'connected' if db_ok else 'error',
    }, status=200 if db_ok else 503)


urlpatterns = [
    # Health & Readiness Probes
    path('health/', health_check, name='health'),
    path('ready/', ready_check, name='ready'),

    # Django Admin
    path('admin/', admin.site.urls),

    # OpenAPI 3 Documentation on /docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API v1 Versioned Endpoints
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/courses/', include('apps.courses.urls')),
    path('api/v1/videos/', include('apps.videos.urls')),
    path('api/v1/tests/', include('apps.assessments.urls')),
]
