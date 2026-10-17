from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from core_api.models import Article

User = get_user_model()


class ArticleAPITests(APITestCase):
    def setUp(self):
        self.articles_url = reverse('article-list')

        # Создаем двух пользователей
        self.author = User.objects.create_user(
            email='author@example.com',
            password='Password123!',
            username='author_user'
        )
        self.other_user = User.objects.create_user(
            email='stranger@example.com',
            password='Password123!',
            username='stranger_user'
        )

        # Создаем статью первого пользователя
        self.article = Article.objects.create(
            title='Введение в Django REST Framework и JWT',
            content='Пошаговое руководство по созданию безопасного API...',
            status=Article.Status.PUBLISHED,
            author=self.author,
            tags='django,drf,jwt'
        )

        # Генерируем JWT токены
        self.author_token = str(RefreshToken.for_user(self.author).access_token)
        self.stranger_token = str(RefreshToken.for_user(self.other_user).access_token)

    def test_public_can_read_articles(self):
        """Неавторизованные пользователи могут читать статьи"""
        response = self.client.get(self.articles_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_unauthenticated_cannot_create_article(self):
        """Неавторизованный запрос на создание статьи возвращает 401"""
        data = {'title': 'Новая статья', 'content': 'Текст...'}
        response = self.client.post(self.articles_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_create_article(self):
        """Авторизованный пользователь создает статью и становится ее автором"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')
        data = {
            'title': 'Продвинутый JWT в Django',
            'content': 'Использование ротации токенов и черного списка.',
            'tags': 'security,tokens'
        }
        response = self.client.post(self.articles_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['author']['email'], self.author.email)

    def test_stranger_cannot_edit_others_article(self):
        """Пользователь не может редактировать чужую статью (IsOwnerOrReadOnly -> 403)"""
        detail_url = reverse('article-detail', kwargs={'pk': self.article.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')

        response = self.client.patch(detail_url, {'title': 'Попытка взлома'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_edit_own_article(self):
        """Автор может успешно обновлять свою публикацию"""
        detail_url = reverse('article-detail', kwargs={'pk': self.article.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.author_token}')

        response = self.client.patch(detail_url, {'title': 'Обновленный заголовок'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Обновленный заголовок')
