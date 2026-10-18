from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Письма: в Docker уходят в MailHog (EMAIL_HOST=mailhog), без него — печатаются в консоль
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=1025)
EMAIL_BACKEND = (
    'django.core.mail.backends.smtp.EmailBackend'
    if EMAIL_HOST
    else 'django.core.mail.backends.console.EmailBackend'
)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@edu.local')
