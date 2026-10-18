from django.contrib import admin

from .models import AttemptAnswer, AttemptEventLog, Test, TestAttempt, TestQuestion


class TestQuestionInline(admin.TabularInline):
    model = TestQuestion
    extra = 0
    raw_id_fields = ('question',)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'mode', 'time_limit_minutes', 'max_attempts')
    list_filter = ('mode',)
    inlines = [TestQuestionInline]


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('test', 'student', 'status', 'score', 'max_score', 'started_at')
    list_filter = ('status',)
    inlines = [AttemptAnswerInline]


admin.site.register(AttemptEventLog)
