from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.organizations.models import Organization


class Topic(TimeStampedModel):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='topics')
    subject = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtopics')

    class Meta:
        db_table = 'topics'
        verbose_name = 'Тема предмета'

    def __str__(self):
        return f"{self.subject} - {self.name}"


class Question(TimeStampedModel):
    class Type(models.TextChoices):
        SINGLE = 'single', 'Один правильный ответ'
        MULTI = 'multi', 'Несколько правильных ответов'
        SHORT = 'short', 'Короткий текст'
        NUMBER = 'number', 'Число с допуском'
        MATCH = 'match', 'Сопоставление'
        OPEN = 'open', 'Развернутый открытый ответ'

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions')
    type = models.CharField(max_length=15, choices=Type.choices)
    text = models.TextField('Текст вопроса (Markdown / LaTeX)')
    explanation = models.TextField('Разбор решения', blank=True)
    difficulty = models.PositiveSmallIntegerField('Сложность (1-5)', default=3)
    tolerance = models.FloatField('Допустимая погрешность для чисел', default=0.0)
    version = models.PositiveIntegerField(default=1)
    is_archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'questions'
        verbose_name = 'Вопрос из банка'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_type_display()}] {self.text[:50]}"


class QuestionOption(TimeStampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.TextField('Текст варианта ответа')
    is_correct = models.BooleanField(default=False)
    match_target = models.CharField('Цель соответствия (для match)', max_length=255, blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'question_options'
        ordering = ['order', 'id']
