from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'user', 'org', 'ip_address', 'entity_type', 'entity_id')
    list_filter = ('action', 'org')
    readonly_fields = [f.name for f in AuditLog._meta.fields]
