from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Кастомный менеджер пользователей, где email используется как уникальный
    идентификатор для аутентификации вместо username.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен для создания пользователя')
        email = self.normalize_email(email)
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
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Кастомная модель пользователя с ролями, биографией и email в качестве логина.
    """
    class Role(models.TextChoices):
        USER = 'USER', 'Пользователь'
        MODERATOR = 'MODERATOR', 'Модератор'
        ADMIN = 'ADMIN', 'Администратор'

    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        help_text='Необязательный псевдоним (никнейм)'
    )
    email = models.EmailField(
        'Email адрес',
        unique=True,
        error_messages={'unique': 'Пользователь с таким email уже существует.'}
    )
    role = models.CharField(
        'Роль в системе',
        max_length=20,
        choices=Role.choices,
        default=Role.USER
    )
    bio = models.TextField('О себе', max_length=500, blank=True)
    is_verified = models.BooleanField(
        'Email подтвержден',
        default=False,
        help_text='Отметка о верификации учетной записи'
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_moderator(self):
        return self.role in [self.Role.MODERATOR, self.Role.ADMIN] or self.is_superuser
