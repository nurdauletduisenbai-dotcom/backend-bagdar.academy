import secrets
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import ValidationError, AuthenticationFailed, PermissionDenied
import jwt
import pyotp

from .models import User, RefreshToken, EmailToken, LoginAttempt, TwoFactorSecret
from apps.organizations.models import OrgMembership, Organization, Invite


def hash_token(token_str: str) -> str:
    return hashlib.sha256(token_str.encode()).hexdigest()


class AuthService:
    ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
    REFRESH_TOKEN_LIFETIME = timedelta(days=30)
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_BLOCK_TIME = 900  # 15 minutes

    @classmethod
    def check_rate_limit(cls, email: str, ip: str):
        cache_key = f"login_attempt:{email}:{ip}"
        attempts = cache.get(cache_key, 0)
        if attempts >= cls.MAX_LOGIN_ATTEMPTS:
            raise PermissionDenied(
                "Слишком много неудачных попыток входа. Попробуйте через 15 минут."
            )

    @classmethod
    def record_login_attempt(cls, email: str, ip: str, success: bool):
        LoginAttempt.objects.create(email=email, ip=ip, success=success)
        cache_key = f"login_attempt:{email}:{ip}"
        if success:
            cache.delete(cache_key)
        else:
            attempts = cache.get(cache_key, 0)
            cache.set(cache_key, attempts + 1, timeout=cls.LOGIN_BLOCK_TIME)

    @classmethod
    def generate_jwt_access_token(cls, user: User, org_id: int = None) -> str:
        now = timezone.now()
        exp = now + cls.ACCESS_TOKEN_LIFETIME
        roles = user.get_roles_for_org(org_id)

        payload = {
            'sub': user.id,
            'email': user.email,
            'org_id': org_id,
            'roles': roles,
            'jti': secrets.token_hex(16),
            'iat': int(now.timestamp()),
            'exp': int(exp.timestamp()),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    @classmethod
    def create_refresh_token(cls, user: User, ip: str = None, device_info: str = '') -> str:
        raw_token = secrets.token_urlsafe(48)
        token_h = hash_token(raw_token)
        expires_at = timezone.now() + cls.REFRESH_TOKEN_LIFETIME

        RefreshToken.objects.create(
            user=user,
            token_hash=token_h,
            device_info=device_info[:255] if device_info else '',
            ip=ip,
            expires_at=expires_at,
        )
        return raw_token

    @classmethod
    def register(cls, email: str, password: str, first_name: str, last_name: str, role: str, org_slug: str, is_minor: bool = False, parent_consent: bool = False) -> User:
        if role not in ['student', 'parent']:
            raise ValidationError("Публичная регистрация доступна только для ролей 'student' или 'parent'.")

        if is_minor and not parent_consent:
            raise ValidationError("Для несовершеннолетних пользователей обязательно согласие родителя.")

        if User.objects.filter(email=email.lower()).exists():
            raise ValidationError({"email": "Пользователь с таким email уже существует."})

        org = Organization.objects.filter(slug=org_slug).first()
        if not org:
            org = Organization.objects.first()

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_minor=is_minor,
            parent_consent=parent_consent,
            is_verified=False
        )

        if org:
            OrgMembership.objects.create(org=org, user=user, role=role)

        cls.send_verification_email(user)
        return user

    @classmethod
    def register_by_invite(cls, invite_token: str, password: str, first_name: str, last_name: str) -> User:
        token_h = hash_token(invite_token)
        invite = Invite.objects.filter(token_hash=token_h).first()
        if not invite or not invite.is_valid:
            raise ValidationError("Приглашение недействительно или срок его действия истек.")

        email = f"invited_{secrets.token_hex(4)}@edu.local"
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_verified=True
        )

        OrgMembership.objects.create(org=invite.org, user=user, role=invite.role)

        if invite.course:
            from apps.courses.models import Enrollment
            Enrollment.objects.create(
                course=invite.course,
                group=invite.group,
                student=user,
                status='active',
                access_until=timezone.now() + timedelta(days=365)
            )

        invite.used_count += 1
        invite.save(update_fields=['used_count'])
        return user

    @classmethod
    def login(cls, email: str, password: str, ip: str, device_info: str, org_id: int = None, totp_code: str = None):
        email_clean = email.lower()
        cls.check_rate_limit(email_clean, ip)

        user = User.objects.filter(email=email_clean, is_active=True).first()
        if not user or not user.check_password(password):
            cls.record_login_attempt(email_clean, ip, success=False)
            raise AuthenticationFailed("Неверный email или пароль.")

        # Проверка 2FA
        two_fa = getattr(user, 'two_factor', None)
        if two_fa and two_fa.is_enabled:
            if not totp_code:
                return {'requires_2fa': True, 'temp_token': cls.generate_jwt_access_token(user)}
            totp = pyotp.TOTP(two_fa.secret_encrypted)
            if not totp.verify(totp_code):
                raise AuthenticationFailed("Неверный код двухфакторной аутентификации.")

        cls.record_login_attempt(email_clean, ip, success=True)

        access_token = cls.generate_jwt_access_token(user, org_id)
        refresh_token = cls.create_refresh_token(user, ip, device_info)

        return {
            'requires_2fa': False,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.get_full_name(),
                'is_verified': user.is_verified,
                'roles': user.get_roles_for_org(org_id),
            }
        }

    @classmethod
    def refresh_tokens(cls, raw_refresh_token: str, ip: str = None, device_info: str = ''):
        token_h = hash_token(raw_refresh_token)
        token_record = RefreshToken.objects.filter(token_hash=token_h).first()

        if not token_record:
            raise AuthenticationFailed("Недействительный refresh токен.")

        # ЗАЩИТА ОТ КРАЖИ ТОКЕНА (Anti-theft / Reuse detection)
        # Если использован уже отозванный токен, отзываем ВСЮ цепочку сессий пользователя!
        if token_record.revoked_at is not None:
            RefreshToken.objects.filter(user=token_record.user, revoked_at__isnull=True).update(
                revoked_at=timezone.now()
            )
            raise AuthenticationFailed(
                "Обнаружена попытка повторного использования отозванного токена. Все сессии пользователя аннулированы в целях безопасности."
            )

        if token_record.expires_at <= timezone.now():
            token_record.revoked_at = timezone.now()
            token_record.save(update_fields=['revoked_at'])
            raise AuthenticationFailed("Срок действия refresh токена истек.")

        # Ротация: сжигаем старый токен и выдаем новый
        new_raw_refresh = secrets.token_urlsafe(48)
        new_hash = hash_token(new_raw_refresh)

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

        new_access = cls.generate_jwt_access_token(token_record.user)
        return {'access_token': new_access, 'refresh_token': new_raw_refresh}

    @classmethod
    def logout(cls, raw_refresh_token: str):
        if not raw_refresh_token:
            return
        token_h = hash_token(raw_refresh_token)
        RefreshToken.objects.filter(token_hash=token_h, revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )

    @classmethod
    def logout_all(cls, user: User):
        RefreshToken.objects.filter(user=user, revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )

    @classmethod
    def send_verification_email(cls, user: User):
        raw_token = secrets.token_urlsafe(32)
        EmailToken.objects.create(
            user=user,
            type=EmailToken.TokenType.VERIFY,
            token_hash=hash_token(raw_token),
            expires_at=timezone.now() + timedelta(hours=24)
        )
        # В фоне Celery отправляет email
        from apps.notifications.tasks import send_email_notification_task
        send_email_notification_task.delay(
            user_id=user.id,
            subject="Подтверждение регистрации на EduPlatform",
            template="verify_email",
            context={'token': raw_token, 'name': user.first_name}
        )

    @classmethod
    def verify_email(cls, raw_token: str) -> bool:
        token_h = hash_token(raw_token)
        token_obj = EmailToken.objects.filter(
            token_hash=token_h,
            type=EmailToken.TokenType.VERIFY,
            used_at__isnull=True,
            expires_at__gt=timezone.now()
        ).first()

        if not token_obj:
            raise ValidationError("Токен подтверждения недействителен или истек.")

        token_obj.used_at = timezone.now()
        token_obj.save(update_fields=['used_at'])

        user = token_obj.user
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        return True
