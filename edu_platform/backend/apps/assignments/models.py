from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.content.models import Lesson


class Assignment(TimeStampedModel):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateTimeField()
    max_score = models.PositiveIntegerField(default=100)

    class Meta:
        db_table = 'assignments'
        verbose_name = 'Домашнее задание'

    def __str__(self):
        return f"{self.lesson.title}: {self.title}"


class AssignmentSubmission(TimeStampedModel):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignment_submissions')
    text_content = models.TextField(blank=True)
    file_url = models.URLField(blank=True, null=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField('Отзыв учителя', blank=True)
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_assignments')
    graded_at = models.DateTimeField(null=True, blank=True)
    can_resubmit = models.BooleanField('Разрешить пересдачу', default=False)

    class Meta:
        db_table = 'assignment_submissions'
        unique_together = ('assignment', 'student')
        verbose_name = 'Сдача задания'
