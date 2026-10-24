from django.contrib import admin

from .models import ContactRequest, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'is_pinned', 'published_at')
    list_filter = ('category', 'is_published', 'is_pinned')
    list_editable = ('is_published', 'is_pinned')
    search_fields = ('title', 'excerpt', 'body')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    readonly_fields = ('author', 'created_at', 'updated_at')
    fields = ('title', 'slug', 'category', 'excerpt', 'body', 'cover',
              'is_published', 'is_pinned', 'published_at', 'author', 'created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'audience', 'language', 'is_processed', 'created_at')
    list_filter = ('is_processed', 'audience', 'language')
    list_editable = ('is_processed',)
    search_fields = ('name', 'phone', 'message')
    readonly_fields = ('name', 'phone', 'audience', 'message', 'language', 'created_at')
    fields = ('name', 'phone', 'audience', 'language', 'message', 'created_at', 'is_processed', 'manager_note')

    def has_add_permission(self, request):
        return False  # заявки приходят только с сайта
