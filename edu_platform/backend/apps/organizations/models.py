from django.conf import settings
from django.db import models

from apps.common.models import SoftDeletableModel, TimeStampedModel


class Organization(SoftDeletableModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    logo_url = models.URLField(blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'organizations'
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'
        ordering = ['name']

    def __str__(self):
        return self.name


class OrgMembership(TimeStampedModel):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Администратор'
        TEACHER = 'teacher', 'Учитель'
        CURATOR = 'curator', 'Куратор'
        STUDENT = 'student', 'Ученик'
        PARENT = 'parent', 'Родитель'

    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'org_memberships'
        unique_together = ('org', 'user', 'role')
        verbose_name = 'Членство в организации'
        verbose_name_plural = 'Членства в организации'

    def __str__(self):
        return f"{self.user} - {self.org.name} ({self.role})"


class Invite(TimeStampedModel):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='invites')
    role = models.CharField(max_length=20, choices=OrgMembership.Role.choices)
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='invites')
    group = models.ForeignKey('courses.Group', on_delete=models.SET_NULL, null=True, blank=True, related_name='invites')
    token_hash = models.CharField(max_length=128, unique=True, db_index=True)
    max_uses = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_invites')

    class Meta:
        db_table = 'invites'
        verbose_name = 'Приглашение'
        verbose_name_plural = 'Приглашения'

    @property
    def is_valid(self):
        from django.utils import timezone
        return self.used_count < self.max_uses and self.expires_at > timezone.now()
