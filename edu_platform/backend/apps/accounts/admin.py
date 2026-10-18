from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import LoginAttempt, ParentStudentRelation, RefreshToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('-created_at',)
    list_display = ('email', 'first_name', 'last_name', 'is_verified', 'is_active', 'is_staff', 'created_at')
    list_filter = ('is_verified', 'is_active', 'is_staff', 'language')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Профиль', {'fields': ('first_name', 'last_name', 'phone', 'language', 'birth_date', 'avatar_url')}),
        ('Статус', {'fields': ('is_verified', 'is_minor', 'parent_consent', 'is_active', 'deleted_at')}),
        ('Права', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'first_name', 'last_name', 'password1', 'password2')}),
    )


@admin.register(ParentStudentRelation)
class ParentStudentRelationAdmin(admin.ModelAdmin):
    list_display = ('parent', 'student', 'is_confirmed', 'created_at')
    list_filter = ('is_confirmed',)


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip', 'device_info', 'created_at', 'expires_at', 'revoked_at')
    list_filter = ('revoked_at',)
    search_fields = ('user__email', 'ip')
    exclude = ('token_hash', 'replaced_by')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('email', 'ip', 'success', 'created_at')
    list_filter = ('success',)
    search_fields = ('email', 'ip')
