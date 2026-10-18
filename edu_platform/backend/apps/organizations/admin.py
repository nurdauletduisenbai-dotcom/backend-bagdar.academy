from django.contrib import admin

from .models import Invite, Organization, OrgMembership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')


@admin.register(OrgMembership)
class OrgMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'org', 'role', 'is_active')
    list_filter = ('org', 'role', 'is_active')
    search_fields = ('user__email',)


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ('org', 'role', 'course', 'used_count', 'max_uses', 'expires_at')
    list_filter = ('org', 'role')
    exclude = ('token_hash',)
