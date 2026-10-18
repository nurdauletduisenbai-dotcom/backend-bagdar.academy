from django.contrib import admin

from .models import Video, VideoProgress


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'youtube_video_id', 'duration_seconds', 'order')


@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'video', 'watched_seconds', 'is_completed', 'last_watched_at')
