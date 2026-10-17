from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Кастомный сериализатор авторизации SimpleJWT.
    Добавляет в полезную нагрузку (payload) токена:
    - email
    - role
    - username
    - is_verified
    А также возвращает объект пользователя в теле ответа.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Кастомные клеймы (Claims) в payload токена
        token['email'] = user.email
        token['role'] = user.role
        token['is_verified'] = user.is_verified
        token['username'] = user.username or ''

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Дополнительная информация в ответе логина
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'username': self.user.username,
            'role': self.user.role,
            'is_verified': self.user.is_verified,
        }
        return data


class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для самостоятельной регистрации пользователей.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password', 'password_confirm', 'bio')
        extra_kwargs = {
            'username': {'required': False},
            'bio': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для профиля текущего авторизованного пользователя.
    """
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'role',
            'bio',
            'is_verified',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'email', 'role', 'is_verified', 'created_at', 'updated_at')


class ChangePasswordSerializer(serializers.Serializer):
    """
    Сериализатор для смены пароля текущим пользователем.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль указан неверно.")
        return value


class LogoutSerializer(serializers.Serializer):
    """
    Сериализатор для выхода из системы с добавлением Refresh токена в черный список (Blacklist).
    """
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            raise serializers.ValidationError({"refresh": "Недействительный или истекший токен."})
