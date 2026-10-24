from django.urls import reverse
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Post


class PostListSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source='get_category_display', read_only=True)
    summary = serializers.CharField(read_only=True)
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ('id', 'slug', 'title', 'category', 'category_label', 'summary', 'cover_url',
                  'is_pinned', 'published_at')

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_cover_url(self, obj) -> str | None:
        # Медиа наружу не публикуется — обложка отдаётся через публичный эндпоинт
        return reverse('news-posts-cover', kwargs={'slug': obj.slug}) if obj.cover else None


class PostDetailSerializer(PostListSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ('body', 'author_name', 'updated_at')

    def get_author_name(self, obj) -> str:
        return obj.author.get_full_name() if obj.author else ''


class PlatformStatsSerializer(serializers.Serializer):
    courses = serializers.IntegerField()
    students = serializers.IntegerField()
    teachers = serializers.IntegerField()
    schools = serializers.IntegerField()
