from django.contrib import admin

from .models import Place


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    # Колонки в списке заведений
    list_display = ('name', 'category', 'address', 'is_published')
    # Галочку «опубликовано» можно менять прямо в списке
    list_editable = ('is_published',)
    # Фильтры справа и строка поиска сверху
    list_filter = ('category', 'is_published')
    search_fields = ('name', 'address')
