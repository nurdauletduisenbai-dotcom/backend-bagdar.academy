import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import RefreshToken
from apps.organizations.models import Organization, OrgMembership

User = get_user_model()


@pytest.mark.django_db
class TestAuthenticationFlows:
    def setup_method(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='Тестовая школа', slug='test-school')

    def test_public_registration_allowed_only_for_student_and_parent(self):
        # Попытка зарегистрироваться как admin публично -> 400
        res = self.client.post('/api/v1/auth/register/', {
            'email': 'hacker@test.com',
            'password': 'StrongPassword123!',
            'first_name': 'Hacker',
            'last_name': 'Test',
            'role': 'admin',
            'org_slug': 'test-school',
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

        # Успешная регистрация как student
        res_ok = self.client.post('/api/v1/auth/register/', {
            'email': 'student@test.com',
            'password': 'StrongPassword123!',
            'first_name': 'Арман',
            'last_name': 'Учеников',
            'role': 'student',
            'org_slug': 'test-school',
        })
        assert res_ok.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email='student@test.com')
        assert user.is_verified is False
        assert OrgMembership.objects.filter(org=self.org, user=user, role='student').exists()

    def test_login_and_refresh_token_rotation(self):
        user = User.objects.create_user(
            email='alice@test.com',
            password='SecretPassword123!',
            first_name='Алиса',
            last_name='Иванова',
            is_verified=True
        )
        OrgMembership.objects.create(org=self.org, user=user, role='student')

        # 1. Логин
        login_res = self.client.post('/api/v1/auth/login/', {
            'email': 'alice@test.com',
            'password': 'SecretPassword123!'
        })
        assert login_res.status_code == status.HTTP_200_OK
        data = login_res.data
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'refresh_token' in login_res.cookies

        first_refresh = data['refresh_token']

        # 2. Обновление токена (Refresh)
        refresh_res = self.client.post('/api/v1/auth/refresh/', {'refresh': first_refresh})
        assert refresh_res.status_code == status.HTTP_200_OK
        new_refresh = refresh_res.data['refresh_token']
        assert new_refresh != first_refresh

        # Старый токен помечен как отозванный
        old_record = RefreshToken.objects.get(user=user, replaced_by__isnull=False)
        assert old_record.revoked_at is not None

    def test_anti_theft_revokes_all_sessions_when_revoked_token_is_replayed(self):
        """
        КРИТЕРИЙ ПРИЕМКИ 4:
        Повторное использование старого refresh-токена отзывает ВСЕ сессии пользователя.
        """
        user = User.objects.create_user(
            email='bob@test.com',
            password='SecretPassword123!',
            first_name='Боб',
            last_name='Смитов'
        )

        login_res = self.client.post('/api/v1/auth/login/', {
            'email': 'bob@test.com',
            'password': 'SecretPassword123!'
        })
        original_refresh = login_res.data['refresh_token']

        # Законный пользователь обновляет токен
        self.client.post('/api/v1/auth/refresh/', {'refresh': original_refresh})

        # Злоумышленник пытается повторно использовать украденный original_refresh токен!
        hijack_res = self.client.post('/api/v1/auth/refresh/', {'refresh': original_refresh})
        assert hijack_res.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Все сессии пользователя аннулированы' in hijack_res.data['error']['message']

        # Проверяем, что ВСЕ сессии пользователя отозваны
        active_sessions_count = RefreshToken.objects.filter(user=user, revoked_at__isnull=True).count()
        assert active_sessions_count == 0
