from django.contrib import admin

from .models import CourseProgress, LessonProgress


@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'percent_completed', 'lessons_completed_count', 'average_test_score')


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'completed_at')
