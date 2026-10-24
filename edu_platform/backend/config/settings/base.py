from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, True),
    DJANGO_SECRET_KEY=(str, 'django-insecure-default-edu-platform-key-change-in-prod'),
    DJANGO_ALLOWED_HOSTS=(list, ['*']),
    CORS_ALLOWED_ORIGINS=(list, ['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:5173']),
)

# Локально: backend/.env или общий edu_platform/.env. В Docker переменные приходят из docker-compose.
for env_file in (BASE_DIR / '.env', BASE_DIR.parent / '.env'):
    if env_file.exists():
        environ.Env.read_env(env_file)
        break

SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env('DJANGO_DEBUG')
ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS')

INSTALLED_APPS = [
    # Django Core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-Party Apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',

    # Platform Apps
    'apps.common.apps.CommonConfig',
    'apps.organizations.apps.OrganizationsConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.courses.apps.CoursesConfig',
    'apps.content.apps.ContentConfig',
    'apps.videos.apps.VideosConfig',
    'apps.questions.apps.QuestionsConfig',
    'apps.assessments.apps.AssessmentsConfig',
    'apps.assignments.apps.AssignmentsConfig',
    'apps.schedule.apps.ScheduleConfig',
    'apps.progress.apps.ProgressConfig',
    'apps.notifications.apps.NotificationsConfig',
    'apps.payments.apps.PaymentsConfig',
    'apps.audit.apps.AuditConfig',
    'apps.news.apps.NewsConfig',
]

MIDDLEWARE = [
    'apps.common.middleware.RequestIDMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.common.middleware.OrgTenantIsolationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database
DATABASES = {
    'default': env.db(
        'DATABASE_URL',
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'
    )
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password Hashers: Argon2id prioritized
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'ru'
LANGUAGES = [
    ('ru', 'Русский'),
    ('kk', 'Қазақша'),
    ('en', 'English'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.common.authentication.TenantJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'apps.common.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    # Ограничение частоты публичных auth-эндпоинтов (по IP)
    'DEFAULT_THROTTLE_RATES': {
        'auth': env('THROTTLE_AUTH_RATE', default='20/min'),
        'auth_refresh': env('THROTTLE_AUTH_REFRESH_RATE', default='60/min'),
    },
}

# SimpleJWT: выпускает и проверяет access-токены.
# Refresh-токены — свои (apps.accounts.models.RefreshToken): хранятся хешем, ротация + защита от повтора.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'UPDATE_LAST_LOGIN': False,
    # Смена пароля сразу делает недействительными все выданные access-токены
    'CHECK_REVOKE_TOKEN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'sub',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# drf-spectacular: Swagger UI на /docs/, ReDoc на /redoc/, схема на /api/schema/
SPECTACULAR_SETTINGS = {
    'TITLE': 'EduPlatform REST API',
    'DESCRIPTION': (
        'Серверная часть образовательной платформы (курсы, видео, тесты, организации).\n\n'
        '**Как авторизоваться в Swagger:**\n'
        '1. `POST /api/v1/auth/login/` с email и паролем (демо: `student1@fizmat.kz` / `StudentPassword123!`).\n'
        '2. Скопируйте `access_token` из ответа.\n'
        '3. Нажмите **Authorize** и вставьте токен (без слова Bearer).\n\n'
        '**Организация:** если пользователь состоит в нескольких организациях, передавайте заголовок '
        '`X-Org-ID`. Доступ к чужой организации — 403, к её объектам — 404.\n\n'
        '**Ошибки** всегда в формате `{"error": {"code", "message", "details"}}`.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/v1',
    'TAGS': [
        {'name': 'auth', 'description': 'Регистрация, вход, refresh-токены, сессии'},
        {'name': '2fa', 'description': 'Двухфакторная аутентификация (TOTP)'},
        {'name': 'users', 'description': 'Профиль текущего пользователя'},
        {'name': 'organizations', 'description': 'Организации пользователя и приглашения'},
        {'name': 'courses', 'description': 'Каталог курсов, содержание, записи учеников'},
        {'name': 'videos', 'description': 'Защищённый доступ к видео и прогресс просмотра'},
        {'name': 'tests', 'description': 'Тесты: конструктор, попытки, ответы, античит, проверка, статистика'},
        {'name': 'content', 'description': 'Разделы, уроки, материалы, комментарии'},
        {'name': 'questions', 'description': 'Банк вопросов и темы организации'},
        {'name': 'assignments', 'description': 'Домашние задания, сдача и проверка работ'},
        {'name': 'schedule', 'description': 'Группы, расписание занятий, посещаемость'},
        {'name': 'notifications', 'description': 'Уведомления, настройки, объявления'},
        {'name': 'payments', 'description': 'Заказы, оплата курсов, возвраты, вебхуки'},
        {'name': 'progress', 'description': 'Прогресс учеников, отчёты для родителей и учителей, сводка'},
        {'name': 'parents', 'description': 'Связь родитель — ученик'},
        {'name': 'audit', 'description': 'Журнал аудита организации'},
    ],
    'ENUM_NAME_OVERRIDES': {
        'OrgRoleEnum': 'apps.organizations.models.OrgMembership.Role',
        'PublicRoleEnum': [('student', 'student'), ('parent', 'parent')],
        'CourseStatusEnum': 'apps.courses.models.Course.Status',
        'CourseTypeEnum': 'apps.courses.models.Course.CourseType',
        'EnrollmentStatusEnum': 'apps.courses.models.Enrollment.Status',
        'QuestionTypeEnum': 'apps.questions.models.Question.Type',
        'AttemptStatusEnum': 'apps.assessments.models.TestAttempt.Status',
        'SubmissionStatusEnum': 'apps.assignments.models.AssignmentSubmission.Status',
        'AttendanceStatusEnum': 'apps.schedule.models.Attendance.Status',
        'OrderStatusEnum': 'apps.payments.models.Order.Status',
        'PaymentProviderEnum': 'apps.payments.models.Order.Provider',
        'NotificationTypeEnum': 'apps.notifications.models.Notification.Type',
        'TestModeEnum': 'apps.assessments.models.Test.Mode',
        'LanguageEnum': 'apps.accounts.models.User.Language',
    },
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
        'filter': True,
        'tryItOutEnabled': True,
        'docExpansion': 'list',
    },
}

# CORS
CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_CREDENTIALS = True

# Redis Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/0'),
        'OPTIONS': {
            'db': '0',
        }
    }
}

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/1')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
# Периодические задачи (сервис beat в docker-compose)
CELERY_BEAT_SCHEDULE = {
    'assignment-deadline-reminders': {
        'task': 'apps.assignments.tasks.send_assignment_deadline_reminders',
        'schedule': 60 * 60,
    },
    'session-reminders': {
        'task': 'apps.schedule.tasks.send_session_reminders',
        'schedule': 5 * 60,
    },
}

# Загрузка файлов (материалы, сдачи заданий). Файлы отдаются только через API с проверкой прав.
MAX_UPLOAD_SIZE_MB = env.int('MAX_UPLOAD_SIZE_MB', default=20)
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Организация по умолчанию для публичной регистрации и адрес фронтенда (ссылки в письмах)
DEFAULT_ORG_SLUG = env('DEFAULT_ORG_SLUG', default='fizmat-school')
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:5173').rstrip('/')

# Platform Feature Flags
FEATURE_PAYMENTS_ENABLED = env.bool('FEATURE_PAYMENTS_ENABLED', True)
FEATURE_GOOGLE_OAUTH_ENABLED = env.bool('FEATURE_GOOGLE_OAUTH_ENABLED', False)
FEATURE_CAPTCHA_ENABLED = env.bool('FEATURE_CAPTCHA_ENABLED', False)
YOUTUBE_API_KEY = env('YOUTUBE_API_KEY', default='')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')
TWO_FACTOR_ENCRYPTION_KEY = env('TWO_FACTOR_ENCRYPTION_KEY', default='dGhpcy1pcy1hLTMyLWJ5dGUtZmVybmV0LWtleS0xMjM=')
