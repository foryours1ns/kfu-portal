from django.contrib import admin
from django.utils.html import format_html

from .models import Meme, MemeVote


@admin.register(Meme)
class MemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'preview', 'caption', 'author', 'is_published', 'created_at')
    list_editable = ('is_published',)
    list_filter = ('is_published',)
    search_fields = ('caption', 'author__username')

    @admin.display(description='превью')
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="48" height="48" style="object-fit: cover; border-radius: 4px;">',
                obj.image.url,
            )
        return '—'


@admin.register(MemeVote)
class MemeVoteAdmin(admin.ModelAdmin):
    list_display = ('meme', 'user', 'value', 'created_at')
    list_filter = ('value',)
    search_fields = ('user__username', 'meme__caption')
