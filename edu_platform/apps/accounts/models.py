from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from apps.common.models import TimeStampedModel, SoftDeletableModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен для создания пользователя')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, SoftDeletableModel):
    class Language(models.TextChoices):
        RU = 'ru', 'Русский'
        KK = 'kk', 'Қазақша'
        EN = 'en', 'English'

    email = models.EmailField('Email адрес', unique=True, db_index=True)
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    phone = models.CharField('Телефон', max_length=30, blank=True, null=True)
    language = models.CharField('Язык интерфейса', max_length=5, choices=Language.choices, default=Language.RU)
    birth_date = models.DateField('Дата рождения', null=True, blank=True)
    avatar_url = models.URLField('Аватар', blank=True, null=True)

    is_verified = models.BooleanField('Email подтвержден', default=False)
    is_minor = models.BooleanField('Младше 14 лет', default=False)
    parent_consent = models.BooleanField('Согласие родителя', default=False)

    is_active = models.BooleanField('Активен', default=True)
    is_staff = models.BooleanField('Персонал', default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_roles_for_org(self, org_id=None):
        """Возвращает список ролей пользователя в рамках организации"""
        if self.is_superuser:
            return ['admin', 'teacher', 'curator', 'student', 'parent']
        qs = self.memberships.filter(is_active=True)
        if org_id:
            qs = qs.filter(org_id=org_id)
        return list(qs.values_list('role', flat=True))


class ParentStudentRelation(TimeStampedModel):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='child_relations')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parent_relations')
    is_confirmed = models.BooleanField(default=False)

    class Meta:
        db_table = 'parent_student_relations'
        unique_together = ('parent', 'student')
        verbose_name = 'Связь Родитель-Ученик'


class RefreshToken(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    device_info = models.CharField(max_length=255, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    replaced_by = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        db_table = 'refresh_tokens'
        verbose_name = 'Сессия (Refresh токен)'
        ordering = ['-created_at']

    @property
    def is_active(self):
        from django.utils import timezone
        return self.revoked_at is None and self.expires_at > timezone.now()


class EmailToken(TimeStampedModel):
    class TokenType(models.TextChoices):
        VERIFY = 'verify', 'Подтверждение email'
        RESET = 'reset', 'Сброс пароля'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_tokens')
    type = models.CharField(max_length=10, choices=TokenType.choices)
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'email_tokens'


class LoginAttempt(models.Model):
    email = models.EmailField(db_index=True)
    ip = models.GenericIPAddressField(db_index=True)
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'login_attempts'
        ordering = ['-created_at']


class TwoFactorSecret(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor')
    secret_encrypted = models.CharField(max_length=255)
    is_enabled = models.BooleanField(default=False)
    backup_codes_hash = models.TextField(help_text='Захешированные резервные коды через запятую')

    class Meta:
        db_table = 'two_factor_secrets'
