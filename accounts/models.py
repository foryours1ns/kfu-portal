from urllib.parse import quote

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.urls import reverse

USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 15

DISPLAY_NAME_MAX_LENGTH = 25
TELEGRAM_MIN_LENGTH = 5
TELEGRAM_MAX_LENGTH = 32
BIO_MAX_LENGTH = 300


def build_letter_avatar_svg(letter):
    """Возвращает data-URI SVG-картинки: светло-серый кружок с буквой по центру."""
    char = (letter or '?')[0].upper()
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 72">'
        '<circle cx="36" cy="36" r="36" fill="#e9ecef"/>'
        '<text x="50%" y="50%" dy="0.35em" text-anchor="middle" '
        'fill="#555" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif" '
        'font-size="30" font-weight="600">'
        f'{char}'
        '</text>'
        '</svg>'
    )
    return f'data:image/svg+xml;utf8,{quote(svg)}'


class User(AbstractUser):
    """Пользователь портала с анкетой студента (имя, институт, Telegram, о себе)."""

    class Faculty(models.TextChoices):
        ITIS = 'itis', 'ИТИС'
        IVMIIT = 'ivmiit', 'ИВМиИТ'
        IUEIF = 'iueif', 'ИУЭиФ'
        LAW = 'law', 'Юридический факультет'
        IMO = 'imo', 'ИМО'
        IFMK = 'ifmk', 'ИФМК'
        PHYSICS = 'physics', 'Институт физики'
        CHEM = 'chem', 'Химический институт'
        IGINGT = 'igingt', 'ИГиНГТ'
        IFMIB = 'ifmib', 'ИФМиБ'
        IMECH = 'imech', 'Институт математики и механики'
        IPO = 'ipo', 'ИПО'
        ISFNMK = 'isfnmk', 'ИСФНиМК'
        II = 'ii', 'Институт искусственного интеллекта'
        OTHER = 'other', 'Другое подразделение КФУ'

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

    display_name = models.CharField(
        'имя',
        max_length=DISPLAY_NAME_MAX_LENGTH,
        blank=True,
    )
    faculty = models.CharField(
        'институт / факультет',
        max_length=20,
        choices=Faculty.choices,
        blank=True,
    )
    telegram = models.CharField(
        'Telegram',
        max_length=TELEGRAM_MAX_LENGTH,
        blank=True,
        validators=[
            MinLengthValidator(
                TELEGRAM_MIN_LENGTH,
                'Юзернейм в Telegram должен быть от 5 до 32 символов.',
            ),
            RegexValidator(
                r'^[A-Za-z0-9_]+$',
                'Юзернейм в Telegram может содержать только латинские буквы, цифры и нижние подчёркивания.',
            ),
        ],
    )
    bio = models.TextField(
        'о себе',
        max_length=BIO_MAX_LENGTH,
        blank=True,
    )
    avatar = models.ImageField(
        'аватар',
        upload_to='avatars/',
        blank=True,
    )

    # Почту не собираем, поэтому createsuperuser о ней не спрашивает
    REQUIRED_FIELDS = []

    def get_absolute_url(self):
        return reverse('accounts:profile', args=[self.username])

    def avatar_url(self):
        """URL загруженного аватара или базовая SVG-картинка с первой буквой логина."""
        if self.avatar:
            return self.avatar.url
        return build_letter_avatar_svg(self.username)
