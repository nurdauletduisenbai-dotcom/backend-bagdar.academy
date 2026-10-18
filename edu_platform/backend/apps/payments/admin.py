from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'course', 'amount', 'currency', 'status', 'provider', 'paid_at', 'created_at')
    list_filter = ('status', 'provider')
    search_fields = ('user__email', 'provider_ref')
    readonly_fields = ('idempotency_key', 'provider_ref', 'paid_at', 'refunded_at')
