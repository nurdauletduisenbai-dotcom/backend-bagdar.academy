from django.contrib import admin

from .models import Assignment, AssignmentSubmission


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'deadline', 'max_score', 'accept_late')
    search_fields = ('title',)


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'status', 'is_late', 'score', 'submitted_at')
    list_filter = ('status', 'is_late')
    search_fields = ('student__email',)
