from django.db import models
from apps.common.models import TimeStampedModel
from apps.courses.models import Enrollment


class CourseProgress(TimeStampedModel):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='progress')
    percent_completed = models.FloatField(default=0.0)
    lessons_completed_count = models.PositiveIntegerField(default=0)
    total_lessons_count = models.PositiveIntegerField(default=0)
    average_test_score = models.FloatField(default=0.0)

    class Meta:
        db_table = 'course_progress'
        verbose_name = 'Прогресс прохождения курса'
