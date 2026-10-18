from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.content.models import Lesson


class Video(TimeStampedModel):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='videos')
    youtube_video_id = models.CharField(max_length=20, db_index=True)
    title = models.CharField(max_length=255)
    duration_seconds = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'videos'
        ordering = ['order', 'id']
        verbose_name = 'Видеоурок (YouTube unlisted)'

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class VideoProgress(TimeStampedModel):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='progresses')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_progresses')
    watched_seconds = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    last_watched_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'video_progress'
        unique_together = ('video', 'student')
        verbose_name = 'Прогресс просмотра видео'
