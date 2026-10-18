from django.conf import settings
from django.db import models

from apps.common.models import SoftDeletableModel, TimeStampedModel
from apps.organizations.models import Organization


class Course(SoftDeletableModel):
    class CourseType(models.TextChoices):
        SCHOOL_SUBJECT = 'school_subject', 'Школьный предмет'
        EXAM_PREP = 'exam_prep', 'Подготовка к экзаменам'
        CLUB = 'club', 'Кружок / Секция'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        PUBLISHED = 'published', 'Опубликован'
        ARCHIVED = 'archived', 'Архивирован'

    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='courses')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=25, choices=CourseType.choices, default=CourseType.SCHOOL_SUBJECT)
    subject = models.CharField(max_length=100, blank=True)
    grade_level = models.PositiveSmallIntegerField('Класс обучения', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    access_days = models.PositiveIntegerField('Доступ после оплаты (дней)', default=365)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    is_free_preview_enabled = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_courses')

    class Meta:
        db_table = 'courses'
        unique_together = ('org', 'slug')
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_type_display()})"


class CourseStaff(TimeStampedModel):
    class StaffRole(models.TextChoices):
        MAIN_TEACHER = 'main_teacher', 'Ведущий преподаватель'
        ASSISTANT = 'assistant', 'Ассистент / Тьютор'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='staff')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_assignments')
    role = models.CharField(max_length=20, choices=StaffRole.choices, default=StaffRole.MAIN_TEACHER)

    class Meta:
        db_table = 'course_staff'
        unique_together = ('course', 'teacher')


class Group(TimeStampedModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=100)
    max_students = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'course_groups'
        verbose_name = 'Группа / Поток'

    def __str__(self):
        return f"{self.course.title} - {self.name}"


class Enrollment(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Активна'
        EXPIRED = 'expired', 'Истекла'
        CANCELED = 'canceled', 'Отменена'
        SUSPENDED = 'suspended', 'Приостановлена'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    access_until = models.DateTimeField('Срок доступа')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'enrollments'
        unique_together = ('course', 'student')
        verbose_name = 'Запись на курс'

    @property
    def is_current_active(self):
        from django.utils import timezone
        return self.status == self.Status.ACTIVE and self.access_until >= timezone.now()
