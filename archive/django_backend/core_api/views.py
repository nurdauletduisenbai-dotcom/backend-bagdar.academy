from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Article
from .serializers import ArticleSerializer
from accounts.permissions import IsOwnerOrReadOnly


class ArticleViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet для работы со статьями.
    - Просмотр доступен всем (включая неавторизованных)
    - Создание требует авторизации по JWT
    - Редактирование и удаление доступны только автору статьи или администратору
    """
    queryset = Article.objects.select_related('author').all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content', 'tags', 'author__email', 'author__username']
    ordering_fields = ['created_at', 'views_count', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())
        tag_param = self.request.query_params.get('tag')
        if tag_param:
            qs = qs.filter(tags__icontains=tag_param)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='my'
    )
    def my_articles(self, request):
        """
        Возвращает список статей, принадлежащих текущему авторизованному пользователю.
        """
        user_articles = self.get_queryset().filter(author=request.user)
        page = self.paginate_queryset(user_articles)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(user_articles, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated, IsOwnerOrReadOnly]
    )
    def publish(self, request, pk=None):
        """
        Публикует черновик статьи.
        """
        article = self.get_object()
        article.status = Article.Status.PUBLISHED
        article.save()
        return Response({
            'detail': f'Статья "{article.title}" успешно опубликована.',
            'status': article.status
        })

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.AllowAny]
    )
    def increment_view(self, request, pk=None):
        """
        Инкрементирует счетчик просмотров статьи.
        """
        article = self.get_object()
        article.views_count += 1
        article.save(update_fields=['views_count'])
        return Response({
            'detail': 'Счетчик просмотров обновлен',
            'views_count': article.views_count
        })
