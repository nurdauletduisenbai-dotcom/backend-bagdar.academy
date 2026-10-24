import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from apps.common.files import UploadTo
from apps.common.models import TimeStampedModel


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True, published_at__lte=timezone.now())


class Post(TimeStampedModel):
    """
    Новость/статья платформы bagdar.academy для публичной главной страницы.
    Не привязана к организации: ведёт суперпользователь через Django admin.
    """

    class Category(models.TextChoices):
        NEWS = 'news', 'Новость'
        ARTICLE = 'article', 'Статья'
        EVENT = 'event', 'Событие'
        UPDATE = 'update', 'Обновление платформы'

    title = models.CharField('Заголовок', max_length=255)
    slug = models.SlugField('Адрес (slug)', max_length=255, unique=True, allow_unicode=True, blank=True,
                            help_text='Часть ссылки /news/<slug>. Пусто — сгенерируется из заголовка.')
    category = models.CharField('Рубрика', max_length=20, choices=Category.choices, default=Category.NEWS)
    excerpt = models.CharField('Анонс', max_length=300, blank=True,
                               help_text='Пара предложений для карточки. Пусто — начало текста.')
    body = models.TextField('Текст', help_text='Обычный текст; пустая строка — новый абзац.')
    cover = models.ImageField('Обложка', upload_to=UploadTo('news'), blank=True)
    is_published = models.BooleanField('Опубликовано', default=False)
    is_pinned = models.BooleanField('Закрепить на главной', default=False)
    published_at = models.DateTimeField('Дата публикации', default=timezone.now, db_index=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='news_posts', verbose_name='Автор')

    objects = PostQuerySet.as_manager()

    class Meta:
        db_table = 'news_posts'
        ordering = ['-is_pinned', '-published_at']
        verbose_name = 'Публикация'
        verbose_name_plural = 'Новости и статьи'

    def __str__(self):
        return self.title

    @property
    def summary(self) -> str:
        if self.excerpt:
            return self.excerpt
        text = ' '.join(self.body.split())
        return text if len(text) <= 220 else text[:217].rsplit(' ', 1)[0] + '…'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)

    def _unique_slug(self) -> str:
        base = slugify(self.title, allow_unicode=True)[:240] or uuid.uuid4().hex[:8]
        slug, n = base, 2
        while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug, n = f'{base}-{n}', n + 1
        return slug


class ContactRequest(TimeStampedModel):
    """Заявка с публичной главной («Остались вопросы?»): менеджер перезванивает."""

    class Audience(models.TextChoices):
        STUDENT = 'student', 'Ученик'
        PARENT = 'parent', 'Родитель'
        SCHOOL = 'school', 'Школа / учебный центр'

    name = models.CharField('Имя', max_length=120)
    phone = models.CharField('Телефон', max_length=32)
    audience = models.CharField('Кто обращается', max_length=20, choices=Audience.choices,
                                default=Audience.STUDENT)
    message = models.TextField('Вопрос', max_length=2000, blank=True)
    language = models.CharField('Язык сайта', max_length=5, blank=True)
    is_processed = models.BooleanField('Обработана', default=False)
    manager_note = models.TextField('Заметка менеджера', blank=True)

    class Meta:
        db_table = 'contact_requests'
        ordering = ['is_processed', '-created_at']
        verbose_name = 'Заявка с сайта'
        verbose_name_plural = 'Заявки с сайта'

    def __str__(self):
        return f'{self.name} · {self.phone}'
