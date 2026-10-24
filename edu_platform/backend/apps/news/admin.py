from django.contrib import admin

from .models import Post


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
