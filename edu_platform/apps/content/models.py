from django.db import models
from django.conf import settings
from apps.common.models import SoftDeletableModel, TimeStampedModel
from apps.courses.models import Course


class Section(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'sections'
        ordering = ['order', 'id']
        verbose_name = 'Раздел курса'

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(SoftDeletableModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    is_free_preview = models.BooleanField('Бесплатный превью-урок', default=False)
    publish_at = models.DateTimeField('Отложенная публикация', null=True, blank=True)

    class Meta:
        db_table = 'lessons'
        ordering = ['order', 'id']
        verbose_name = 'Урок'

    def __str__(self):
        return f"{self.section.title}: {self.title}"

    @property
    def is_published(self):
        from django.utils import timezone
        return self.publish_at is None or self.publish_at <= timezone.now()


class Material(TimeStampedModel):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=255)
    file_url = models.URLField()
    file_type = models.CharField(max_length=50, blank=True)
    file_size_bytes = models.BigIntegerField(default=0)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'materials'
        ordering = ['order']
        verbose_name = 'Учебный материал (S3)'


class Comment(TimeStampedModel):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    is_hidden = models.BooleanField(default=False)

    class Meta:
        db_table = 'comments'
        ordering = ['created_at']
        verbose_name = 'Комментарий / Вопрос к уроку'
