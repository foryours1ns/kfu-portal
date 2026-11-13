from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

# Показываем пользователей в админке так же, как стандартных пользователей Django
admin.site.register(User, UserAdmin)
