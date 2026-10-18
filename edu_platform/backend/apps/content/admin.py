from django.contrib import admin

from .models import Comment, Lesson, Material, Section


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'order', 'is_free_preview', 'publish_at')
    list_filter = ('is_free_preview',)


admin.site.register(Material)
admin.site.register(Comment)
