from django.db import models
from django.conf import settings
from apps.common.models import TimeStampedModel
from apps.courses.models import Group


class Session(TimeStampedModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    online_meeting_url = models.URLField('Ссылка на онлайн-урок (Zoom/Meet)', blank=True, null=True)

    class Meta:
        db_table = 'group_sessions'
        ordering = ['start_time']
        verbose_name = 'Занятие группы'


class Attendance(TimeStampedModel):
    class Status(models.TextChoices):
        PRESENT = 'present', 'Присутствовал'
        ABSENT = 'absent', 'Отсутствовал'
        LATE = 'late', 'Опоздал'
        EXCUSED = 'excused', 'Уважительная причина'

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PRESENT)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'attendances'
        unique_together = ('session', 'student')
        verbose_name = 'Посещаемость'
