from django.contrib import admin

from .models import Question, QuestionOption, Topic


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'type', 'topic', 'difficulty', 'is_archived')
    list_filter = ('type', 'difficulty', 'is_archived')
    search_fields = ('text',)
    inlines = [QuestionOptionInline]


admin.site.register(Topic)
