from django.db import models
from django.conf import settings
from apps.common.models import TimeStampedModel
from apps.organizations.models import Organization
from apps.courses.models import Course


class Announcement(TimeStampedModel):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='announcements')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='announcements')
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        db_table = 'announcements'
        ordering = ['-created_at']
        verbose_name = 'Объявление'


class Notification(TimeStampedModel):
    class Type(models.TextChoices):
        ASSIGNMENT_NEW = 'assignment_new', 'Новое задание'
        ASSIGNMENT_DEADLINE = 'assignment_deadline', 'Приближение дедлайна'
        ASSIGNMENT_GRADED = 'assignment_graded', 'Задание проверено'
        TEST_RESULT = 'test_result', 'Результат теста'
        SESSION_START = 'session_start', 'Начало занятия'
        COMMENT_REPLY = 'comment_reply', 'Ответ на комментарий'
        SYSTEM = 'system', 'Системное уведомление'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        verbose_name = 'Уведомление'


class NotificationPreference(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    email_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)

    class Meta:
        db_table = 'notification_preferences'
