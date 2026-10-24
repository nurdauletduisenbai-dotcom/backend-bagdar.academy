import re

from django.urls import reverse
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import ContactRequest, Post


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


class ContactRequestSerializer(serializers.ModelSerializer):
    consent = serializers.BooleanField(write_only=True, help_text='Согласие на обработку персональных данных')

    class Meta:
        model = ContactRequest
        fields = ('name', 'phone', 'audience', 'message', 'language', 'consent')

    def validate_phone(self, value):
        digits = re.sub(r'\D', '', value)
        if not 10 <= len(digits) <= 15:
            raise serializers.ValidationError('Укажите номер телефона, например +7 700 000 00 00.')
        return value.strip()

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError('Укажите имя.')
        return value

    def validate_language(self, value):
        return value if value in ('kk', 'ru') else ''

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError('Нужно согласие на обработку персональных данных.')
        return value

    def create(self, validated_data):
        validated_data.pop('consent')
        return super().create(validated_data)
