from django.conf import settings
from django.db import models

from apps.organizations.models import Organization


class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN = 'login', 'Вход в систему'
        LOGOUT = 'logout', 'Выход'
        PASSWORD_CHANGE = 'password_change', 'Смена пароля'
        ROLE_CHANGE = 'role_change', 'Изменение ролей'
        COURSE_CREATE = 'course_create', 'Создание курса'
        COURSE_DELETE = 'course_delete', 'Удаление курса'
        GRADE_CHANGE = 'grade_change', 'Изменение оценки'
        PERSONAL_DATA_ACCESS = 'personal_data_access', 'Доступ к персональным данным'

    org = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='audit_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=40, choices=Action.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_id = models.CharField(max_length=64, blank=True)
    entity_type = models.CharField(max_length=50, blank=True)
    entity_id = models.PositiveIntegerField(null=True, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        verbose_name = 'Журнал аудита'
