import hashlib
import secrets
from datetime import timedelta

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, ValidationError
from rest_framework_simplejwt.tokens import AccessToken

from apps.audit.services import AuditService
from apps.common.tenancy import resolve_org_id
from apps.organizations.models import Invite, Organization, OrgMembership

from .models import EmailToken, LoginAttempt, RefreshToken, TwoFactorSecret, User


def hash_token(token_str: str) -> str:
    return hashlib.sha256(token_str.encode()).hexdigest()


def _fernet() -> Fernet:
    return Fernet(settings.TWO_FACTOR_ENCRYPTION_KEY)


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()


def decrypt_secret(secret_encrypted: str) -> str:
    try:
        return _fernet().decrypt(secret_encrypted.encode()).decode()
    except InvalidToken as exc:
        raise AuthenticationFailed('Секрет 2FA повреждён. Обратитесь к администратору.') from exc


class AuthService:
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_BLOCK_TIME = 900  # 15 минут

    @classmethod
    def refresh_lifetime(cls) -> timedelta:
        return settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']

    # ---------- Лимит попыток входа ----------

    @classmethod
    def check_rate_limit(cls, email: str, ip: str):
        if cache.get(f"login_attempt:{email}:{ip}", 0) >= cls.MAX_LOGIN_ATTEMPTS:
            raise PermissionDenied('Слишком много неудачных попыток входа. Попробуйте через 15 минут.')

    @classmethod
    def record_login_attempt(cls, email: str, ip: str, success: bool):
        LoginAttempt.objects.create(email=email, ip=ip, success=success)
        cache_key = f"login_attempt:{email}:{ip}"
        if success:
            cache.delete(cache_key)
        else:
            cache.set(cache_key, cache.get(cache_key, 0) + 1, timeout=cls.LOGIN_BLOCK_TIME)

    # ---------- Токены ----------

    @classmethod
    def generate_jwt_access_token(cls, user: User, org_id: int | None = None) -> str:
        """Access-токен SimpleJWT (его же проверяет TenantJWTAuthentication) с ролями организации."""
        token = AccessToken.for_user(user)
        token['email'] = user.email
        token['org_id'] = org_id
        token['roles'] = user.get_roles_for_org(org_id)
        return str(token)

    @classmethod
    def create_refresh_token(cls, user: User, ip: str | None = None, device_info: str = '',
                             org_id: int | None = None) -> str:
        raw_token = secrets.token_urlsafe(48)
        RefreshToken.objects.create(
            user=user,
            token_hash=hash_token(raw_token),
            device_info=(device_info or '')[:255],
            ip=ip,
            org_id=org_id,
            expires_at=timezone.now() + cls.refresh_lifetime(),
        )
        return raw_token

    @classmethod
    def user_payload(cls, user: User, org_id: int | None) -> dict:
        memberships = user.memberships.filter(is_active=True).select_related('org')
        organizations: dict[int, dict] = {}
        for m in memberships:
            org = organizations.setdefault(m.org_id, {'id': m.org_id, 'name': m.org.name, 'slug': m.org.slug, 'roles': []})
            org['roles'].append(m.role)
        return {
            'id': user.id,
            'email': user.email,
            'full_name': user.get_full_name(),
            'is_verified': user.is_verified,
            'org_id': org_id,
            'roles': user.get_roles_for_org(org_id),
            'organizations': list(organizations.values()),
        }

    # ---------- Регистрация ----------

    @classmethod
    @transaction.atomic
    def register(cls, email: str, password: str, first_name: str, last_name: str, role: str = 'student',
                 org_slug: str | None = None, is_minor: bool = False, parent_consent: bool = False) -> User:
        if role not in ('student', 'parent'):
            raise ValidationError("Публичная регистрация доступна только для ролей 'student' или 'parent'.")
        if is_minor and not parent_consent:
            raise ValidationError('Для несовершеннолетних пользователей обязательно согласие родителя.')

        email = email.lower()
        if User.all_objects.filter(email=email).exists():
            raise ValidationError({'email': 'Пользователь с таким email уже существует.'})

        org = Organization.objects.filter(slug=org_slug or settings.DEFAULT_ORG_SLUG, is_active=True).first()
        if not org:
            raise ValidationError({'org_slug': 'Организация не найдена.'})

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_minor=is_minor,
            parent_consent=parent_consent,
            is_verified=False,
        )
        OrgMembership.objects.create(org=org, user=user, role=role)
        transaction.on_commit(lambda: cls.send_verification_email(user))
        return user

    @classmethod
    @transaction.atomic
    def register_by_invite(cls, invite_token: str, email: str, password: str, first_name: str, last_name: str) -> User:
        invite = Invite.objects.select_for_update().filter(token_hash=hash_token(invite_token)).first()
        if not invite or not invite.is_valid:
            raise ValidationError('Приглашение недействительно или срок его действия истек.')

        email = email.lower()
        if User.all_objects.filter(email=email).exists():
            raise ValidationError({'email': 'Пользователь с таким email уже существует. Войдите в аккаунт.'})

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_verified=True,
        )
        OrgMembership.objects.create(org=invite.org, user=user, role=invite.role)

        if invite.course and invite.role == OrgMembership.Role.STUDENT:
            from apps.courses.models import Enrollment
            Enrollment.objects.get_or_create(
                course=invite.course,
                student=user,
                defaults={
                    'group': invite.group,
                    'status': Enrollment.Status.ACTIVE,
                    'access_until': timezone.now() + timedelta(days=365),
                },
            )

        invite.used_count += 1
        invite.save(update_fields=['used_count'])
        return user

    # ---------- Вход / выход ----------

    @classmethod
    def login(cls, email: str, password: str, ip: str, device_info: str, org_id: int | None = None,
              totp_code: str | None = None) -> dict:
        email_clean = email.lower()
        cls.check_rate_limit(email_clean, ip)

        user = User.objects.filter(email=email_clean, is_active=True).first()
        if not user or not user.check_password(password):
            cls.record_login_attempt(email_clean, ip, success=False)
            raise AuthenticationFailed('Неверный email или пароль.')

        two_fa = TwoFactorSecret.objects.filter(user=user, is_enabled=True).first()
        if two_fa:
            # Без кода токены не выдаём: клиент повторяет вход с email + password + totp_code
            if not totp_code:
                return {'requires_2fa': True}
            if not TwoFactorService.verify_code(two_fa, totp_code):
                cls.record_login_attempt(email_clean, ip, success=False)
                raise AuthenticationFailed('Неверный код двухфакторной аутентификации.')

        current_org_id = resolve_org_id(user, org_id)
        cls.record_login_attempt(email_clean, ip, success=True)
        AuditService.log(AuditService.Action.LOGIN, user=user, org_id=current_org_id, ip=ip)

        return {
            'requires_2fa': False,
            'access_token': cls.generate_jwt_access_token(user, current_org_id),
            'refresh_token': cls.create_refresh_token(user, ip, device_info, current_org_id),
            'user': cls.user_payload(user, current_org_id),
        }

    @classmethod
    def refresh_tokens(cls, raw_refresh_token: str | None, ip: str | None = None, device_info: str = '',
                       org_id: int | None = None) -> dict:
        if not raw_refresh_token:
            raise AuthenticationFailed('Refresh токен не передан.')

        with transaction.atomic():
            token_record = (
                RefreshToken.objects.select_for_update()
                .select_related('user')
                .filter(token_hash=hash_token(raw_refresh_token))
                .first()
            )
            if not token_record:
                raise AuthenticationFailed('Недействительный refresh токен.')

            # Защита от кражи: повторное использование уже заменённого (ротированного) токена
            # отзывает ВСЕ сессии пользователя
            reuse_detected = token_record.revoked_at is not None and token_record.replaced_by is not None
            if reuse_detected:
                RefreshToken.objects.filter(user=token_record.user, revoked_at__isnull=True).update(
                    revoked_at=timezone.now()
                )

        if reuse_detected:
            raise AuthenticationFailed(
                'Обнаружена попытка повторного использования отозванного токена. '
                'Все сессии пользователя аннулированы в целях безопасности.'
            )

        if token_record.revoked_at is not None:
            raise AuthenticationFailed('Сессия завершена. Войдите заново.')

        user = token_record.user
        now = timezone.now()
        if token_record.expires_at <= now or not user.is_active or user.is_deleted:
            token_record.revoked_at = now
            token_record.save(update_fields=['revoked_at'])
            raise AuthenticationFailed('Срок действия refresh токена истек.')

        current_org_id = resolve_org_id(user, org_id or token_record.org_id)

        new_raw_refresh = secrets.token_urlsafe(48)
        new_hash = hash_token(new_raw_refresh)
        token_record.revoked_at = now
        token_record.replaced_by = new_hash
        token_record.save(update_fields=['revoked_at', 'replaced_by'])

        RefreshToken.objects.create(
            user=user,
            token_hash=new_hash,
            device_info=(device_info or token_record.device_info)[:255],
            ip=ip or token_record.ip,
            org_id=current_org_id,
            expires_at=now + cls.refresh_lifetime(),
        )
        return {
            'access_token': cls.generate_jwt_access_token(user, current_org_id),
            'refresh_token': new_raw_refresh,
        }

    @classmethod
    def logout(cls, raw_refresh_token: str | None):
        if not raw_refresh_token:
            return
        RefreshToken.objects.filter(token_hash=hash_token(raw_refresh_token), revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )

    @classmethod
    def logout_all(cls, user: User):
        RefreshToken.objects.filter(user=user, revoked_at__isnull=True).update(revoked_at=timezone.now())

    # ---------- Email ----------

    @classmethod
    def send_verification_email(cls, user: User):
        raw_token = secrets.token_urlsafe(32)
        EmailToken.objects.create(
            user=user,
            type=EmailToken.TokenType.VERIFY,
            token_hash=hash_token(raw_token),
            expires_at=timezone.now() + timedelta(hours=24),
        )
        from apps.notifications.tasks import send_email_notification_task
        send_email_notification_task.delay(
            user_id=user.id,
            subject='Подтверждение регистрации на EduPlatform',
            template='verify_email',
            context={'link': f"{settings.FRONTEND_URL}/api/v1/auth/verify-email/?token={raw_token}"},
        )

    @classmethod
    def verify_email(cls, raw_token: str | None) -> bool:
        token_obj = None
        if raw_token:
            token_obj = EmailToken.objects.filter(
                token_hash=hash_token(raw_token),
                type=EmailToken.TokenType.VERIFY,
                used_at__isnull=True,
                expires_at__gt=timezone.now(),
            ).select_related('user').first()
        if not token_obj:
            raise ValidationError('Токен подтверждения недействителен или истек.')

        token_obj.used_at = timezone.now()
        token_obj.save(update_fields=['used_at'])
        token_obj.user.is_verified = True
        token_obj.user.save(update_fields=['is_verified'])
        return True


class TwoFactorService:
    ISSUER = 'EduPlatform'
    BACKUP_CODES_COUNT = 8

    @classmethod
    def setup(cls, user: User) -> dict:
        """Создаёт (или пересоздаёт) секрет. 2FA включается только после подтверждения кодом."""
        existing = TwoFactorSecret.objects.filter(user=user).first()
        if existing and existing.is_enabled:
            raise ValidationError('2FA уже включена. Сначала отключите её.')

        secret = pyotp.random_base32()
        TwoFactorSecret.objects.update_or_create(
            user=user,
            defaults={'secret_encrypted': encrypt_secret(secret), 'is_enabled': False, 'backup_codes_hash': ''},
        )
        return {
            'secret': secret,
            'otpauth_uri': pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=cls.ISSUER),
        }

    @classmethod
    def enable(cls, user: User, code: str) -> list[str]:
        two_fa = TwoFactorSecret.objects.filter(user=user).first()
        if not two_fa:
            raise ValidationError('Сначала вызовите настройку 2FA.')
        if two_fa.is_enabled:
            raise ValidationError('2FA уже включена.')
        if not pyotp.TOTP(decrypt_secret(two_fa.secret_encrypted)).verify(code, valid_window=1):
            raise ValidationError({'code': 'Неверный код.'})

        backup_codes = [secrets.token_hex(4) for _ in range(cls.BACKUP_CODES_COUNT)]
        two_fa.backup_codes_hash = ','.join(hash_token(c) for c in backup_codes)
        two_fa.is_enabled = True
        two_fa.save(update_fields=['backup_codes_hash', 'is_enabled', 'updated_at'])
        return backup_codes

    @classmethod
    def disable(cls, user: User, password: str, code: str):
        two_fa = TwoFactorSecret.objects.filter(user=user, is_enabled=True).first()
        if not two_fa:
            raise ValidationError('2FA не включена.')
        if not user.check_password(password):
            raise ValidationError({'password': 'Неверный пароль.'})
        if not cls.verify_code(two_fa, code):
            raise ValidationError({'code': 'Неверный код.'})
        two_fa.delete()

    @classmethod
    def verify_code(cls, two_fa: TwoFactorSecret, code: str) -> bool:
        """TOTP-код или одноразовый резервный код (сгорает после использования)."""
        code = (code or '').strip().replace(' ', '')
        if pyotp.TOTP(decrypt_secret(two_fa.secret_encrypted)).verify(code, valid_window=1):
            return True

        hashes = [h for h in two_fa.backup_codes_hash.split(',') if h]
        code_hash = hash_token(code.lower())
        if code_hash in hashes:
            hashes.remove(code_hash)
            two_fa.backup_codes_hash = ','.join(hashes)
            two_fa.save(update_fields=['backup_codes_hash', 'updated_at'])
            return True
        return False
