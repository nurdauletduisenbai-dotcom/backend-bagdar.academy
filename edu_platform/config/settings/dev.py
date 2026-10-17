from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Console email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
