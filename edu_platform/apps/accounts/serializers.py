from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, RefreshToken, TwoFactorSecret


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    role = serializers.ChoiceField(choices=['student', 'parent'], default='student')
    org_slug = serializers.CharField(required=False, default='default-school')
    is_minor = serializers.BooleanField(default=False)
    parent_consent = serializers.BooleanField(default=False)


class RegisterByInviteSerializer(serializers.Serializer):
    invite_token = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    totp_code = serializers.CharField(required=False, allow_blank=True)


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()


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
        read_only_fields = ('id', 'email', 'is_verified', 'created_at', 'roles')

    def get_roles(self, obj):
        request = self.context.get('request')
        org_id = getattr(request, 'org_id', None) if request else None
        return obj.get_roles_for_org(org_id)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])


class SessionSerializer(serializers.ModelSerializer):
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = RefreshToken
        fields = ('id', 'device_info', 'ip', 'created_at', 'expires_at', 'is_current')

    def get_is_current(self, obj):
        return False
