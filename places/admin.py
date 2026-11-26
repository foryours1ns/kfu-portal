from django.contrib import admin

from accounts.models import Notification

from .models import Place, Review


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    # Колонки в списке заведений
    list_display = ('name', 'category', 'address', 'is_published')
    # Галочку «опубликовано» можно менять прямо в списке
    list_editable = ('is_published',)
    # Фильтры справа и строка поиска сверху
    list_filter = ('category', 'is_published')
    search_fields = ('name', 'address')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('place', 'author', 'rating', 'is_published', 'created_at')
    list_editable = ('is_published',)
    list_filter = ('is_published', 'rating')
    search_fields = ('place__name', 'author__username', 'text')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change and 'is_published' in form.changed_data and obj.author_id:
            action = 'опубликовал' if obj.is_published else 'скрыл'
            Notification.objects.create(
                recipient=obj.author,
                message=f'Модератор {action} ваш отзыв о заведении «{obj.place.name}»',
                link=obj.place.get_absolute_url(),
            )

    def delete_model(self, request, obj):
        if obj.author_id:
            Notification.objects.create(
                recipient=obj.author,
                message=f'Модератор удалил ваш отзыв о заведении «{obj.place.name}»',
                link=obj.place.get_absolute_url(),
            )
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset.select_related('author', 'place'):
            if obj.author_id:
                Notification.objects.create(
                    recipient=obj.author,
                    message=f'Модератор удалил ваш отзыв о заведении «{obj.place.name}»',
                    link=obj.place.get_absolute_url(),
                )
        super().delete_queryset(request, queryset)
