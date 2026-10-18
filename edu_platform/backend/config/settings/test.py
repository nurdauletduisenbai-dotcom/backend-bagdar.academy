from .base import *

DEBUG = False
ALLOWED_HOSTS = ['*']

# Тесты не должны зависеть от запущенного Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Celery-задачи выполняются синхронно, без брокера
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Быстрый хешер паролей для тестов
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
