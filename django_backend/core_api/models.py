import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Article(models.Model):
    """
    Модель статьи/публикации для демонстрации защищенного CRUD API в DRF.
    """
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Черновик'
        PUBLISHED = 'PUBLISHED', 'Опубликовано'
        ARCHIVED = 'ARCHIVED', 'В архиве'

    title = models.CharField('Заголовок', max_length=200)
    slug = models.SlugField('ЧПУ (Slug)', max_length=220, unique=True, blank=True)
    content = models.TextField('Содержимое')
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='Автор'
    )
    views_count = models.PositiveIntegerField('Просмотры', default=0)
    tags = models.CharField('Теги (через запятую)', max_length=200, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True) or 'article'
            self.slug = f"{base_slug[:180]}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"
