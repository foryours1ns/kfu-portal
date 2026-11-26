from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from accounts.models import Notification

from .models import Meme, MemeComment, MemeVote


def _meme_label(meme):
    if meme.caption:
        return f'мем «{meme.caption[:40]}»'
    return 'мем'


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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change and 'is_published' in form.changed_data:
            label = _meme_label(obj)
            if obj.is_published:
                Notification.objects.create(
                    recipient=obj.author,
                    message=f'Модератор опубликовал ваш {label}',
                    link=f"{reverse('memes:list')}#meme-{obj.pk}",
                )
            else:
                Notification.objects.create(
                    recipient=obj.author,
                    message=f'Модератор скрыл ваш {label}',
                    link=reverse('memes:list'),
                )

    def delete_model(self, request, obj):
        action = 'удалил' if obj.is_published else 'отклонил'
        Notification.objects.create(
            recipient=obj.author,
            message=f'Модератор {action} ваш {_meme_label(obj)}',
            link=reverse('memes:list'),
        )
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset.select_related('author'):
            action = 'удалил' if obj.is_published else 'отклонил'
            Notification.objects.create(
                recipient=obj.author,
                message=f'Модератор {action} ваш {_meme_label(obj)}',
                link=reverse('memes:list'),
            )
        super().delete_queryset(request, queryset)


@admin.register(MemeVote)
class MemeVoteAdmin(admin.ModelAdmin):
    list_display = ('meme', 'user', 'value', 'created_at')
    list_filter = ('value',)
    search_fields = ('user__username', 'meme__caption')


@admin.register(MemeComment)
class MemeCommentAdmin(admin.ModelAdmin):
    list_display = ('meme', 'author', 'text', 'created_at')
    search_fields = ('author__username', 'text', 'meme__caption')
