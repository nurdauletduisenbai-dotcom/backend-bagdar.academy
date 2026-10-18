from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import RefreshToken, User
from .services import hash_token

# ---------- Запросы ----------

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    role = serializers.ChoiceField(choices=['student', 'parent'], default='student')
    org_slug = serializers.CharField(required=False, help_text='Slug организации; по умолчанию DEFAULT_ORG_SLUG')
    is_minor = serializers.BooleanField(default=False)
    parent_consent = serializers.BooleanField(default=False)


class RegisterByInviteSerializer(serializers.Serializer):
    invite_token = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    totp_code = serializers.CharField(required=False, allow_blank=True, help_text='Код 2FA или резервный код')


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, help_text='Можно не передавать — берётся из cookie refresh_token')


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, help_text='Можно не передавать — берётся из cookie refresh_token')


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class TwoFactorCodeSerializer(serializers.Serializer):
    code = serializers.CharField()


class TwoFactorDisableSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    code = serializers.CharField()


# ---------- Ответы ----------

class OrganizationBriefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    roles = serializers.ListField(child=serializers.CharField())


class AuthUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    is_verified = serializers.BooleanField()
    org_id = serializers.IntegerField(allow_null=True)
    roles = serializers.ListField(child=serializers.CharField())
    organizations = OrganizationBriefSerializer(many=True)


class LoginResponseSerializer(serializers.Serializer):
    requires_2fa = serializers.BooleanField()
    access_token = serializers.CharField(required=False)
    refresh_token = serializers.CharField(required=False)
    user = AuthUserSerializer(required=False)


class TokenPairSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()


class TwoFactorSetupResponseSerializer(serializers.Serializer):
    secret = serializers.CharField()
    otpauth_uri = serializers.CharField(help_text='Показать как QR-код в приложении-аутентификаторе')


class TwoFactorBackupCodesSerializer(serializers.Serializer):
    message = serializers.CharField()
    backup_codes = serializers.ListField(child=serializers.CharField())


class UserProfileSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'phone',
            'language',
            'birth_date',
            'avatar_url',
            'is_verified',
            'is_minor',
            'roles',
            'created_at',
        )
        read_only_fields = ('id', 'email', 'is_verified', 'is_minor', 'created_at', 'roles')

    def get_roles(self, obj) -> list[str]:
        request = self.context.get('request')
        org_id = getattr(request, 'org_id', None) if request else None
        return obj.get_roles_for_org(org_id)


class RegisterResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    user = UserProfileSerializer()


class SessionSerializer(serializers.ModelSerializer):
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = RefreshToken
        fields = ('id', 'device_info', 'ip', 'created_at', 'expires_at', 'is_current')

    def get_is_current(self, obj) -> bool:
        raw = self.context.get('current_refresh')
        return bool(raw) and obj.token_hash == hash_token(raw)
