from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 15


class User(AbstractUser):
    """Пользователь портала.

    Берём стандартного пользователя Django и меняем только правила для логина.
    Позже сюда же добавим поля профиля (имя, факультет).
    """

    username = models.CharField(
        'логин',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[
            MinLengthValidator(
                USERNAME_MIN_LENGTH,
                'Логин должен быть от 3 до 15 символов.',
            ),
            RegexValidator(
                r'^[A-Za-z0-9_]+$',
                'Логин может содержать только латинские буквы, цифры и нижние подчёркивания.',
            ),
        ],
        error_messages={'unique': 'Этот логин уже занят.'},
    )

    # Почту не собираем, поэтому createsuperuser о ней не спрашивает
    REQUIRED_FIELDS = []
