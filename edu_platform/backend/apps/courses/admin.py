from django.contrib import admin

from .models import Course, CourseStaff, Enrollment, Group


class CourseStaffInline(admin.TabularInline):
    model = CourseStaff
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'org', 'type', 'status', 'price', 'created_at')
    list_filter = ('org', 'type', 'status')
    search_fields = ('title', 'subject')
    inlines = [CourseStaffInline]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'max_students', 'is_active')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'access_until', 'enrolled_at')
    list_filter = ('status', 'course')
    search_fields = ('student__email',)
