from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.content.models import Lesson
from apps.courses.models import Course
from apps.questions.models import Question


class Test(TimeStampedModel):
    class Mode(models.TextChoices):
        PRACTICE = 'practice', 'Практика (без таймера)'
        QUIZ = 'quiz', 'Квиз / Проверочная'
        EXAM = 'exam', 'Экзамен'
        MOCK_EXAM = 'mock_exam', 'Пробный экзамен'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='tests')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='tests')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    mode = models.CharField(max_length=15, choices=Mode.choices, default=Mode.QUIZ)

    time_limit_minutes = models.PositiveIntegerField('Лимит времени (мин)', default=30)
    max_attempts = models.PositiveIntegerField('Макс. попыток', default=2)
    passing_score_pct = models.PositiveSmallIntegerField('Проходной процент', default=70)

    shuffle_questions = models.BooleanField(default=True)
    shuffle_options = models.BooleanField(default=True)
    show_answers_after_submit = models.BooleanField('Показывать ответы после сдачи', default=True)

    available_from = models.DateTimeField(null=True, blank=True)
    available_to = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tests'
        verbose_name = 'Тест'

    def __str__(self):
        return f"{self.title} [{self.get_mode_display()}]"


class TestQuestion(TimeStampedModel):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='test_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='in_tests')
    order = models.PositiveIntegerField(default=1)
    points = models.FloatField(default=1.0)

    class Meta:
        db_table = 'test_questions'
        unique_together = ('test', 'question')
        ordering = ['order', 'id']


class TestAttempt(TimeStampedModel):
    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'В процессе'
        SUBMITTED = 'submitted', 'Сдана'
        EXPIRED = 'expired', 'Время истекло'
        GRADED = 'graded', 'Оценена'

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='test_attempts')
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.IN_PROGRESS)

    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)

    score = models.FloatField(default=0.0)
    max_score = models.FloatField(default=0.0)
    score_pct = models.FloatField(default=0.0)
    is_passed = models.BooleanField(default=False)

    class Meta:
        db_table = 'test_attempts'
        ordering = ['-started_at']
        verbose_name = 'Попытка прохождения теста'


class AttemptAnswer(TimeStampedModel):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.JSONField('Выбранные ID вариантов или сопоставления', default=list, blank=True)
    text_answer = models.TextField('Ответ текстом или числом', blank=True)

    score = models.FloatField(default=0.0)
    is_correct = models.BooleanField(default=False)
    auto_graded = models.BooleanField(default=True)
    teacher_feedback = models.TextField(blank=True)

    class Meta:
        db_table = 'attempt_answers'
        unique_together = ('attempt', 'question')


class AttemptEventLog(TimeStampedModel):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='event_logs')
    event_type = models.CharField(max_length=50)  # tab_blur, window_resize, copy_paste
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'attempt_event_logs'
