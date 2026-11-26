from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Notification, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'display_name', 'faculty', 'telegram', 'is_staff')
    list_filter = ('faculty', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'display_name', 'telegram')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Профиль студента', {'fields': ('avatar', 'display_name', 'faculty', 'telegram', 'bio')}),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('recipient__username', 'message')
