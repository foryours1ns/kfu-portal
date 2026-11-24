from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'display_name', 'faculty', 'telegram', 'is_staff')
    list_filter = ('faculty', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'display_name', 'telegram')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Профиль студента', {'fields': ('avatar', 'display_name', 'faculty', 'telegram', 'bio')}),
    )
