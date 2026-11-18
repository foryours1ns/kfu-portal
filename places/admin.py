from django.contrib import admin

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
