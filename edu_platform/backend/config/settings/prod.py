from .base import *

DEBUG = False

# Strict Security Headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# На сервере http -> https перенаправляет nginx; здесь — подстраховка (выключается до выпуска сертификата)
SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', True)
SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT
SECURE_HSTS_SECONDS = 31536000 if SECURE_SSL_REDIRECT else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Django-админка за nginx: origin-ы, с которых принимаются POST-формы
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Почта: SMTP, если задан EMAIL_HOST, иначе письма пишутся в лог (journalctl -u bagdar-backend)
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', True)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@bagdar.academy')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_BACKEND = (
    'django.core.mail.backends.smtp.EmailBackend'
    if EMAIL_HOST
    else 'django.core.mail.backends.console.EmailBackend'
)

# Ошибки в stdout -> systemd journal
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'WARNING'},
}
