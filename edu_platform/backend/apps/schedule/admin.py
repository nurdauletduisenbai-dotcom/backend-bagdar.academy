from django.contrib import admin

from .models import Attendance, Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'start_time', 'end_time', 'is_canceled')
    list_filter = ('is_canceled', 'group__course')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('session', 'student', 'status')
    list_filter = ('status',)
