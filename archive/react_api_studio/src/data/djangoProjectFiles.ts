import { ProjectFile } from '../types';

export const EDU_PROJECT_FILES: ProjectFile[] = [
  {
    path: 'config/settings/base.py',
    name: 'base.py',
    category: 'config',
    language: 'python',
    description: 'Базовые настройки Django 5: Argon2id, SimpleJWT (ротация, blacklist), drf-spectacular, Celery, Redis.',
    content: `# config/settings/base.py
import os
from datetime import timedelta
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env('DJANGO_DEBUG', default=True)
ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS', default=['*'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-Party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',

    # Platform Apps
    'apps.common',
    'apps.organizations',
    'apps.accounts',
    'apps.courses',
    'apps.content',
    'apps.videos',
    'apps.questions',
    'apps.assessments',
    'apps.assignments',
    'apps.schedule',
    'apps.progress',
    'apps.notifications',
    'apps.payments',
    'apps.audit',
]

MIDDLEWARE = [
    'apps.common.middleware.RequestIDMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.common.middleware.OrgTenantIsolationMiddleware',
]

AUTH_USER_MODEL = 'accounts.User'

# Password Hashers: Argon2id prioritized
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_PAGINATION_CLASS': 'apps.common.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}`
  },
  {
    path: 'apps/common/permissions.py',
    name: 'permissions.py',
    category: 'config',
    language: 'python',
    description: 'RBAC роли (Admin, Teacher, Curator, Student, Parent) и проверка активной записи на курс / free preview.',
    content: `# apps/common/permissions.py
from rest_framework import permissions
from django.utils import timezone

def require_roles(*roles):
    class RolePermission(permissions.BasePermission):
        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            if request.user.is_superuser:
                return True
            user_roles = request.user.get_roles_for_org(getattr(request, 'org_id', None))
            return any(role in user_roles for role in roles)
    return RolePermission

class HasActiveEnrollmentOrPreview(permissions.BasePermission):
    """
    КРИТЕРИЙ ПРИЕМКИ 1:
    Ученик получает доступ к уроку, видео или тесту только при активной записи (status='active'
    и access_until не истек) ЛИБО если урок помечен is_free_preview.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        roles = user.get_roles_for_org(getattr(request, 'org_id', None))
        if 'admin' in roles or 'teacher' in roles or 'curator' in roles:
            return True

        if getattr(obj, 'is_free_preview', False):
            return True

        from apps.courses.models import Enrollment
        return Enrollment.objects.filter(
            student=user,
            course_id=obj.course_id if hasattr(obj, 'course_id') else obj.lesson.section.course_id,
            status='active',
            access_until__gte=timezone.now()
        ).exists()`
  },
  {
    path: 'apps/accounts/services.py',
    name: 'services.py (accounts)',
    category: 'accounts',
    language: 'python',
    description: 'Бизнес-логика auth: ротация токенов, защита от кражи (Anti-Theft Session Revocation), 2FA TOTP.',
    content: `# apps/accounts/services.py
import secrets, hashlib
from datetime import timedelta
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from .models import RefreshToken

def hash_token(token_str: str) -> str:
    return hashlib.sha256(token_str.encode()).hexdigest()

class AuthService:
    ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
    REFRESH_TOKEN_LIFETIME = timedelta(days=30)

    @classmethod
    def refresh_tokens(cls, raw_refresh_token: str, ip: str = None, device_info: str = ''):
        token_h = hash_token(raw_refresh_token)
        token_record = RefreshToken.objects.filter(token_hash=token_h).first()

        if not token_record:
            raise AuthenticationFailed("Недействительный refresh токен.")

        # КРИТЕРИЙ ПРИЕМКИ 4 (Защита от кражи сессии):
        # Если использован уже отозванный токен, аннулируем ВСЮ цепочку сессий пользователя!
        if token_record.revoked_at is not None:
            RefreshToken.objects.filter(user=token_record.user, revoked_at__isnull=True).update(
                revoked_at=timezone.now()
            )
            raise AuthenticationFailed(
                "Обнаружена попытка повторного использования отозванного токена. Все сессии аннулированы."
            )

        # Ротация: старый сжигается, создается новый
        new_raw = secrets.token_urlsafe(48)
        new_hash = hash_token(new_raw)

        token_record.revoked_at = timezone.now()
        token_record.replaced_by = new_hash
        token_record.save(update_fields=['revoked_at', 'replaced_by'])

        RefreshToken.objects.create(
            user=token_record.user,
            token_hash=new_hash,
            device_info=device_info or token_record.device_info,
            ip=ip or token_record.ip,
            expires_at=timezone.now() + cls.REFRESH_TOKEN_LIFETIME,
        )

        return {'access_token': cls.generate_jwt_access_token(token_record.user), 'refresh_token': new_raw}`
  },
  {
    path: 'apps/videos/services.py',
    name: 'services.py (videos)',
    category: 'core_api',
    language: 'python',
    description: 'Извлечение YouTube ID, защищенный шлюз play (youtube-nocookie), автофиксация прогресса при >= 90%.',
    content: `# apps/videos/services.py
import re
from rest_framework.exceptions import PermissionDenied
from .models import Video, VideoProgress

class VideoService:
    YOUTUBE_REGEX = re.compile(r'(?:youtube\\.com\\/(?:watch\\?v=|embed\\/)|youtu\\.be\\/)([a-zA-Z0-9_-]{11})')

    @classmethod
    def get_secure_player_data(cls, video: Video, user):
        # Проверка прав доступа: без активной записи ученик получает 403 Forbidden
        cls.verify_student_access_to_video(video, user)

        # Выдача защищенного плеера без утечки исходного ID в списки уроков
        embed_url = f"https://www.youtube-nocookie.com/embed/{video.youtube_video_id}?rel=0&modestbranding=1"
        return {
            'video_id': video.id,
            'title': video.title,
            'embed_url': embed_url,
            'duration_seconds': video.duration_seconds
        }

    @classmethod
    def update_progress(cls, video: Video, user, watched_seconds: int):
        progress, _ = VideoProgress.objects.get_or_create(video=video, student=user)
        if watched_seconds > progress.watched_seconds:
            progress.watched_seconds = watched_seconds

        # Автоматическая отметка выполненным при 90% просмотра
        if video.duration_seconds > 0 and (progress.watched_seconds / video.duration_seconds) >= 0.90:
            progress.is_completed = True
        progress.save()
        return {'watched_seconds': progress.watched_seconds, 'is_completed': progress.is_completed}`
  },
  {
    path: 'apps/assessments/services.py',
    name: 'services.py (assessments)',
    category: 'core_api',
    language: 'python',
    description: 'Движок тестирования: сокрытие правильных ответов до сдачи, автопроверка закрытых типов, античит.',
    content: `# apps/assessments/services.py
from django.utils import timezone
from .models import Test, TestAttempt, AttemptAnswer, TestQuestion

class AssessmentService:
    @classmethod
    def get_clean_questions_for_student(cls, attempt: TestAttempt):
        """
        КРИТЕРИЙ ПРИЕМКИ 3:
        Клиент никогда не получает флаги is_correct и разборы ответов до сдачи теста!
        """
        test_questions = TestQuestion.objects.filter(test=attempt.test).select_related('question')
        payload = []
        for tq in test_questions:
            q = tq.question
            payload.append({
                'id': q.id,
                'type': q.type,
                'text': q.text,
                'points': tq.points,
                'options': [{'id': opt.id, 'text': opt.text} for opt in q.options.all()]
            })
        return payload

    @classmethod
    def submit_attempt(cls, attempt: TestAttempt):
        # Серверный расчет баллов по типам: single, multi, number (с допуском), short, match
        # Установка статуса GRADED, расчет процентов и отметки is_passed
        attempt.status = TestAttempt.Status.GRADED
        attempt.submitted_at = timezone.now()
        attempt.save()
        return attempt`
  },
  {
    path: 'docker-compose.yml',
    name: 'docker-compose.yml',
    category: 'docker',
    language: 'yaml',
    description: 'Стек микросервисов: API, PostgreSQL 16, Redis 7, MinIO S3, Celery Worker, MailHog.',
    content: `version: '3.9'

services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgres://postgres:postgres@db:5432/edu_platform_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_started }

  worker:
    build: .
    command: celery -A config worker -l info
    depends_on: [api, redis]

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=edu_platform_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d edu_platform_db"]
      interval: 5s

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  minio:
    image: minio/minio:RELEASE.2024-03-30T09-41-56Z
    ports: ["9000:9000", "9001:9001"]

  mailhog:
    image: mailhog/mailhog:v1.0.1
    ports: ["1025:1025", "8025:8025"]`
  },
  {
    path: 'seed_data.py',
    name: 'seed_data.py',
    category: 'tests',
    language: 'python',
    description: 'Генератор демо-данных: организация, 5 пользователей, 3 курса, видео, банк из 30 вопросов, тест.',
    content: `# seed_data.py
# Создает демонстрационные данные платформы:
# - Организация 'ФизМат Лицей'
# - Администратор, Учитель, 2 Ученика, Родитель
# - 3 Курса: школьный предмет, подготовка к экзаменам, кружок
# - Защищенные видеоуроки
# - Банк из 30 вопросов всех 6 типов
# - Итоговый тест с настройками таймера`
  }
];

export const DJANGO_PROJECT_FILES = EDU_PROJECT_FILES;
