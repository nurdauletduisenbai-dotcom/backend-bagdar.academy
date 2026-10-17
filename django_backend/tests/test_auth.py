from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class JWTAuthenticationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('auth_register')
        self.token_url = reverse('token_obtain_pair')
        self.token_refresh_url = reverse('token_refresh')
        self.profile_url = reverse('user_profile')
        self.logout_url = reverse('auth_logout')

        self.user_data = {
            'email': 'developer@example.com',
            'username': 'devuser',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
            'bio': 'Full-stack software engineer'
        }

    def test_user_registration(self):
        """Тест успешной регистрации пользователя с возвратом JWT пары"""
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['user']['email'], self.user_data['email'])

    def test_token_obtain_and_claims(self):
        """Тест получения JWT токена и проверки кастомных claims"""
        # Сначала создаем пользователя
        user = User.objects.create_user(
            email='alice@example.com',
            password='SecretPassword123!',
            role=User.Role.USER
        )

        login_data = {
            'email': 'alice@example.com',
            'password': 'SecretPassword123!'
        }
        response = self.client.post(self.token_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'alice@example.com')

    def test_protected_profile_endpoint_with_bearer_token(self):
        """Тест доступа к защищенному эндпоинту профиля по Bearer токену"""
        user = User.objects.create_user(
            email='bob@example.com',
            password='SecretPassword123!',
            bio='Python developer'
        )
        login_res = self.client.post(self.token_url, {
            'email': 'bob@example.com',
            'password': 'SecretPassword123!'
        })
        access_token = login_res.data['access']

        # 1. Запрос БЕЗ токена -> 401
        res_no_auth = self.client.get(self.profile_url)
        self.assertEqual(res_no_auth.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. Запрос С токеном в заголовке Authorization -> 200
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        res_auth = self.client.get(self.profile_url)
        self.assertEqual(res_auth.status_code, status.HTTP_200_OK)
        self.assertEqual(res_auth.data['email'], 'bob@example.com')
        self.assertEqual(res_auth.data['bio'], 'Python developer')

    def test_token_refresh_and_rotation(self):
        """Тест обновления Access токена через Refresh токен"""
        user = User.objects.create_user(
            email='carol@example.com',
            password='SecretPassword123!'
        )
        login_res = self.client.post(self.token_url, {
            'email': 'carol@example.com',
            'password': 'SecretPassword123!'
        })
        refresh_token = login_res.data['refresh']

        refresh_res = self.client.post(self.token_refresh_url, {'refresh': refresh_token})
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_res.data)

    def test_logout_and_token_blacklisting(self):
        """Тест выхода из системы и добавления refresh токена в черный список"""
        user = User.objects.create_user(
            email='david@example.com',
            password='SecretPassword123!'
        )
        login_res = self.client.post(self.token_url, {
            'email': 'david@example.com',
            'password': 'SecretPassword123!'
        })
        access_token = login_res.data['access']
        refresh_token = login_res.data['refresh']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_res = self.client.post(self.logout_url, {'refresh': refresh_token})
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

        # Попытка обновить уже заблокированный токен должна вызывать 401
        retry_res = self.client.post(self.token_refresh_url, {'refresh': refresh_token})
        self.assertEqual(retry_res.status_code, status.HTTP_401_UNAUTHORIZED)
