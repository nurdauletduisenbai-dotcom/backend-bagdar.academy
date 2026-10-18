from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Article

User = get_user_model()


class AuthorSummarySerializer(serializers.ModelSerializer):
    """
    Компактное представление автора статьи.
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'role')


class ArticleSerializer(serializers.ModelSerializer):
    """
    Основной сериализатор статей.
    Автор автоматически привязывается к текущему авторизованному пользователю.
    """
    author = AuthorSummarySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Article
        fields = (
            'id',
            'title',
            'slug',
            'content',
            'status',
            'status_display',
            'author',
            'views_count',
            'tags',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'slug', 'author', 'views_count', 'created_at', 'updated_at')

    def create(self, validated_data):
        # Привязываем автора из контекста запроса
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['author'] = request.user
        return super().create(validated_data)
